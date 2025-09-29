from __future__ import annotations

import io
import os
import re
import tempfile
from typing import Any, Dict, List, Optional, Tuple

import duckdb
import httpx
from langchain.tools import tool
from langchain_ollama import ChatOllama


def _download_to_temp(url: str) -> str:
    with httpx.stream("GET", url, follow_redirects=True, timeout=60) as r:
        r.raise_for_status()
        fd, path = tempfile.mkstemp(suffix=".csv")
        with os.fdopen(fd, "wb") as f:
            for chunk in r.iter_bytes():
                f.write(chunk)
    return path


def _open_duckdb_with_csv(csv_path: str) -> duckdb.DuckDBPyConnection:
    conn = duckdb.connect(database=":memory:")
    # Use DuckDB's CSV reader. Parameters are auto-detected.
    conn.execute(
        """
        CREATE OR REPLACE VIEW data AS
        SELECT * FROM read_csv_auto(?, IGNORE_ERRORS=true);
        """,
        [csv_path],
    )
    return conn


def _inspect_schema_and_sample(conn: duckdb.DuckDBPyConnection) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    schema_rows = conn.execute("DESCRIBE data").fetchall()
    schema = [
        {"column": r[0], "type": r[1]} for r in schema_rows
    ]
    sample_df = conn.execute("SELECT * FROM data LIMIT 20").fetch_df()
    sample = sample_df.to_dict(orient="records")
    return schema, sample


def _propose_sql(question: str, schema: List[Dict[str, Any]], sample: List[Dict[str, Any]]) -> str:
    llm = ChatOllama(model=os.getenv("CSV_SQL_MODEL", "llama3.2:latest"))
    schema_text = "\n".join([f"- {c['column']}: {c['type']}" for c in schema])
    sample_preview = sample[:5]
    prompt = (
        "You are a data analyst. Write a single SELECT SQL query for DuckDB over a table named 'data'.\n"
        "Constraints: No DDL/DML. Add LIMIT 50 if not present. Use valid DuckDB SQL only.\n\n"
        f"Schema:\n{schema_text}\n\n"
        f"Sample rows (first 5):\n{sample_preview}\n\n"
        f"Question: {question}\n\n"
        "Return ONLY the SQL."
    )
    result = llm.invoke(prompt)
    text = getattr(result, "content", str(result))
    # Extract SQL inside fences if present
    code_match = re.search(r"```sql\s*([\s\S]*?)```", text, flags=re.IGNORECASE)
    sql = code_match.group(1).strip() if code_match else text.strip()
    # Keep a single statement, strip trailing semicolon
    sql = sql.split(";")[0].strip()
    # Basic safety: must start with SELECT
    if not re.match(r"^SELECT\s", sql, flags=re.IGNORECASE):
        sql = "SELECT * FROM data LIMIT 50"
    # Enforce LIMIT <= 100
    if re.search(r"\blimit\b\s*(\d+)", sql, flags=re.IGNORECASE):
        sql = re.sub(r"\blimit\b\s*(\d+)", lambda m: f"LIMIT {min(int(m.group(1)), 100)}", sql, flags=re.IGNORECASE)
    else:
        sql = f"{sql} LIMIT 50"
    return sql


def _execute_sql(conn: duckdb.DuckDBPyConnection, sql: str) -> Tuple[List[str], List[List[Any]]]:
    rel = conn.execute(sql)
    df = rel.fetch_df()
    columns = list(df.columns)
    rows = df.values.tolist()
    return columns, rows


@tool("analyze_csv", return_direct=False)
def analyze_csv(
    file_url: Optional[str] = None,
    file_path: Optional[str] = None,
    question: str = "",
) -> Dict[str, Any]:
    """
    Analyze a CSV using DuckDB and NL-to-SQL.

    Args:
        file_url: Public or signed URL to the CSV file.
        file_path: Local container path to the CSV (e.g., from a shared volume).
        question: Natural language question to answer using SQL over table 'data'.

    Returns:
        JSON payload with schema, sample, chosen_sql, rows (limited), columns, and a brief summary.
    """
    if not (file_url or file_path):
        return {"error": "Provide file_url or file_path"}

    temp_path = None
    try:
        csv_path = file_path
        if not csv_path:
            temp_path = _download_to_temp(file_url)  # type: ignore[arg-type]
            csv_path = temp_path

        conn = _open_duckdb_with_csv(csv_path)
        schema, sample = _inspect_schema_and_sample(conn)

        sql = _propose_sql(question or "Show first rows", schema, sample)
        columns: List[str]
        rows: List[List[Any]]
        try:
            columns, rows = _execute_sql(conn, sql)
        except Exception as ex:
            # On failure, fall back to a safe default
            sql = "SELECT * FROM data LIMIT 50"
            columns, rows = _execute_sql(conn, sql)
            return {
                "schema": schema,
                "sample": sample,
                "chosen_sql": sql,
                "columns": columns,
                "rows": rows,
                "warning": f"SQL generation failed, returned fallback. Error: {str(ex)}",
            }

        return {
            "schema": schema,
            "sample": sample,
            "chosen_sql": sql,
            "columns": columns,
            "rows": rows,
            "summary": f"Returned {len(rows)} rows and {len(columns)} columns.",
        }
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
