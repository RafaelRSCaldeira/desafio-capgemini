import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

try:
    from sentence_transformers import CrossEncoder
    CROSS_ENCODER_AVAILABLE = True
except Exception:
    CrossEncoder = None  # type: ignore
    CROSS_ENCODER_AVAILABLE = False


class CSVChunkProcessor:
    """Ingests CSV files into a vector database with high-accuracy retrieval.

    Features:
    - Dual indexing: cell-level chunks and row-window chunks.
    - Every chunk includes the original CSV header for context.
    - Optional cross-encoder re-ranking for improved accuracy.
    - Returns the original file name with each search result.
    """

    def __init__(
        self,
        embedding_model_name: str = "all-MiniLM-L6-v2",
        cross_encoder_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    ) -> None:
        self.embedder = SentenceTransformer(embedding_model_name)
        self.embedding_dim = self.embedder.get_sentence_embedding_dimension()
        self.cross_encoder_name = cross_encoder_name
        self.cross_encoder = None
        if CROSS_ENCODER_AVAILABLE:
            try:
                self.cross_encoder = CrossEncoder(cross_encoder_name)
            except Exception:
                self.cross_encoder = None

    # ---------------------------
    # Chunking helpers
    # ---------------------------
    @staticmethod
    def _header_line(df: pd.DataFrame) -> str:
        return ",".join([str(c) for c in df.columns.tolist()])

    @staticmethod
    def _row_as_csv(df: pd.DataFrame, idx: int) -> str:
        values = ["" if pd.isna(v) else str(v) for v in df.iloc[idx].tolist()]
        return ",".join(values)

    def _cell_chunk_text(
        self,
        df: pd.DataFrame,
        row_idx: int,
        col_name: str,
        csv_filename: str,
        id_column: str,
    ) -> Tuple[str, Dict[str, Any]]:
        header = self._header_line(df)
        row_csv = self._row_as_csv(df, row_idx)
        value = df.iloc[row_idx][col_name]
        value_str = "[valor não disponível]" if pd.isna(value) else str(value)
        row_id = (
            df.iloc[row_idx][id_column]
            if id_column in df.columns
            else row_idx + 1
        )

        text = (
            f"CSV: {csv_filename}\n"
            f"Header: {header}\n"
            f"Row ID: {row_id} | Column: {col_name}\n"
            f"Value: {value_str}\n"
            f"Row: {row_csv}"
        )
        payload = {
            "csv_file": csv_filename,
            "row_id": int(row_id) if isinstance(row_id, (int, np.integer)) else str(row_id),
            "column_name": col_name,
            "row_index": int(row_idx),
            "original_value": None if pd.isna(value) else value_str,
            "chunk_type": "cell",
        }
        return text, payload

    def _row_window_chunk_text(
        self,
        df: pd.DataFrame,
        start_row: int,
        end_row: int,
        csv_filename: str,
    ) -> Tuple[str, Dict[str, Any]]:
        header = self._header_line(df)
        window_lines = [self._row_as_csv(df, i) for i in range(start_row, end_row)]
        window_preview = "\n".join(window_lines)
        text = (
            f"CSV: {csv_filename}\n"
            f"Header: {header}\n"
            f"Rows {start_row + 1}-{end_row}:\n{window_preview}"
        )
        payload = {
            "csv_file": csv_filename,
            "row_start": int(start_row),
            "row_end": int(end_row - 1),
            "chunk_type": "row_window",
        }
        return text, payload

    # ---------------------------
    # Public API: build chunks
    # ---------------------------
    def build_chunks(
        self,
        df: pd.DataFrame,
        csv_filename: str,
        start_chunk_id: int = 1,
        id_column: str = "id",
        rows_per_window: int = 20,
        include_cell_chunks: bool = True,
        include_row_windows: bool = True,
    ) -> List[Dict[str, Any]]:
        chunks: List[Dict[str, Any]] = []
        chunk_id = start_chunk_id

        # 1) Cell-level chunks (fine-grained, great for precision)
        if include_cell_chunks:
            for row_idx in range(len(df)):
                for col_name in df.columns:
                    if col_name == id_column:
                        continue
                    text, payload = self._cell_chunk_text(
                        df=df,
                        row_idx=row_idx,
                        col_name=col_name,
                        csv_filename=csv_filename,
                        id_column=id_column,
                    )
                    chunks.append({
                        "id": chunk_id,
                        "text": text,
                        "metadata": payload,
                    })
                    chunk_id += 1

        # 2) Row-window chunks (coarser, improves recall and gives context)
        if include_row_windows and rows_per_window > 0:
            total_rows = len(df)
            for start in range(0, total_rows, rows_per_window):
                end = min(start + rows_per_window, total_rows)
                text, payload = self._row_window_chunk_text(
                    df=df,
                    start_row=start,
                    end_row=end,
                    csv_filename=csv_filename,
                )
                chunks.append({
                    "id": chunk_id,
                    "text": text,
                    "metadata": payload,
                })
                chunk_id += 1

        return chunks

    # ---------------------------
    # Embeddings and upsert
    # ---------------------------
    def generate_embeddings(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        texts = [c["text"] for c in chunks]
        embeddings = self.embedder.encode(texts, show_progress_bar=False)
        for i, c in enumerate(chunks):
            c["embedding"] = embeddings[i].tolist()
        return chunks

    @staticmethod
    def to_qdrant_points(chunks: List[Dict[str, Any]]) -> List[PointStruct]:
        return [
            PointStruct(id=c["id"], vector=c["embedding"], payload=c["metadata"])  # type: ignore[arg-type]
            for c in chunks
        ]

    def process_csv_to_qdrant(
        self,
        csv_path: str,
        collection_name: str,
        client: Optional[QdrantClient] = None,
        start_chunk_id: int = 1,
        id_column: str = "id",
        rows_per_window: int = 20,
        include_cell_chunks: bool = True,
        include_row_windows: bool = True,
    ) -> Dict[str, Any]:
        if client is None:
            client = QdrantClient(path=Path(__file__).parent / "db")

        # Load CSV
        df = pd.read_csv(csv_path)
        csv_filename = Path(csv_path).name

        # Ensure collection exists
        try:
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=self.embedding_dim, distance=Distance.COSINE),
            )
        except Exception:
            pass

        # Build chunks
        chunks = self.build_chunks(
            df=df,
            csv_filename=csv_filename,
            start_chunk_id=start_chunk_id,
            id_column=id_column,
            rows_per_window=rows_per_window,
            include_cell_chunks=include_cell_chunks,
            include_row_windows=include_row_windows,
        )

        # Embed and upsert
        chunks = self.generate_embeddings(chunks)
        points = self.to_qdrant_points(chunks)
        client.upsert(collection_name=collection_name, points=points)

        return {
            "csv_path": csv_path,
            "csv_filename": csv_filename,
            "collection_name": collection_name,
            "total_chunks": len(points),
            "total_rows": int(len(df)),
            "total_columns": int(len(df.columns)),
            "embedding_dimension": int(self.embedding_dim),
        }


def process_csvs_as_chunks(
    csv_paths: Optional[List[str]] = None,
    collection_name: str = "csv_chunks",
    id_column: str = "id",
    rows_per_window: int = 20,
    include_cell_chunks: bool = True,
    include_row_windows: bool = True,
):
    processor = CSVChunkProcessor()
    client = QdrantClient(path=Path(__file__).parent / "db")

    results: List[Dict[str, Any]] = []
    global_chunk_id = 1

    if csv_paths is None:
        csv_folder = os.path.join(os.path.dirname(__file__), "archives")
        csv_paths = [
            os.path.join(csv_folder, file)
            for file in os.listdir(csv_folder)
            if file.lower().endswith(".csv")
        ]

    for csv_path in csv_paths:
        try:
            print(f"[PROC] Processando {csv_path}...")
            result = processor.process_csv_to_qdrant(
                csv_path=csv_path,
                collection_name=collection_name,
                client=client,
                start_chunk_id=global_chunk_id,
                id_column=id_column,
                rows_per_window=rows_per_window,
                include_cell_chunks=include_cell_chunks,
                include_row_windows=include_row_windows,
            )
            results.append(result)
            global_chunk_id += result["total_chunks"]
            print(
                f"[OK] {csv_path}: {result['total_chunks']} chunks | "
                f"{result['total_rows']} linhas × {result['total_columns']} colunas"
            )
        except Exception as e:
            print(f"[ERRO] {csv_path}: {e}")
            results.append({"csv_path": csv_path, "error": str(e)})

    return results, client


def find_top_k_semantic(
    text: str,
    client: QdrantClient,
    k: int = 10,
    collection_name: str = "csv_chunks",
    prefetch: int = 30,
) -> List[Dict[str, Any]]:
    """Semantic search with optional cross-encoder re-ranking.

    Returns a list of dicts with: file, score, chunk_type, snippet, and metadata.
    """
    processor = CSVChunkProcessor()
    query_vec = processor.embedder.encode([text])[0].tolist()

    prefetch = max(prefetch, k)
    raw = client.query_points(
        collection_name=collection_name,
        query=query_vec,
        limit=prefetch,
    ).points

    candidates: List[Dict[str, Any]] = []
    for r in raw:
        payload = r.payload or {}
        candidates.append({
            "file": payload.get("csv_file"),
            "score": float(getattr(r, "score", 0.0)),
            "chunk_type": payload.get("chunk_type"),
            "snippet": payload,  # full payload context
            "text": None,  # not stored as payload to keep payload small
            "id": r.id,
        })

    # Fetch texts for re-ranking from the DB is not trivial with Qdrant payload-only; we kept
    # the informative formatted text inside the embedding input but not in payload to save space.
    # For re-ranking, we can reconstruct a text representation from payload fields:
    def payload_to_text(p: Dict[str, Any]) -> str:
        if p.get("chunk_type") == "cell":
            header = "(header omitted in payload)"
            row_id = p.get("row_id")
            col = p.get("column_name")
            value = p.get("original_value") or "[valor não disponível]"
            return f"Row ID: {row_id} | Column: {col} | Value: {value}"
        if p.get("chunk_type") == "row_window":
            return (
                f"Rows {p.get('row_start')}–{p.get('row_end')} in file {p.get('csv_file')}"
            )
        return f"File: {p.get('csv_file')}"

    # Re-rank with cross-encoder if available
    if processor.cross_encoder is not None and len(candidates) > 1:
        pairs = [(text, payload_to_text(c["snippet"])) for c in candidates]
        try:
            scores = processor.cross_encoder.predict(pairs).tolist()  # type: ignore[union-attr]
            for i, s in enumerate(scores):
                candidates[i]["score"] = float(s)
            candidates.sort(key=lambda x: x["score"], reverse=True)
        except Exception:
            # Fallback: keep original order
            pass

    return candidates[:k]


def _load_df_for_file(csv_filename: str) -> pd.DataFrame:
    """Load a CSV by filename from the default archives folder."""
    csv_path = os.path.join(os.path.dirname(__file__), "archives", csv_filename)
    return pd.read_csv(csv_path)


def _format_row_with_header(df: pd.DataFrame, row_idx: int) -> str:
    """Return a compact, readable row: "col1: v1 | col2: v2 | ..."""
    parts = []
    for col in df.columns:
        val = df.iloc[row_idx][col]
        if pd.isna(val):
            val_str = "[valor não disponível]"
        else:
            val_str = str(val)
        parts.append(f"{col}: {val_str}")
    return " | ".join(parts)


def find_top_k_rows(
    text: str,
    client: QdrantClient,
    k: int = 10,
    collection_name: str = "csv_chunks",
    prefetch: int = 50,
) -> List[Dict[str, Any]]:
    """Row-level semantic search.

    - Retrieves top candidates (cell and row-window) from vector DB
    - Aggregates scores per (csv_file, row_index)
    - Re-ranks (optional cross-encoder already applied in candidate selection)
    - Returns the full row with headers as a formatted string plus original file
    """
    # First, get a broader set of candidates
    candidates = find_top_k_semantic(
        text=text,
        client=client,
        k=max(k, 10),
        collection_name=collection_name,
        prefetch=max(prefetch, 50),
    )

    # Aggregate per (file, row_index)
    row_scores: Dict[Tuple[str, int], float] = {}
    # Track which files are involved
    files_set = set()

    for c in candidates:
        payload = c.get("snippet") or {}
        file = payload.get("csv_file")
        if not file:
            continue
        files_set.add(file)
        score = float(c.get("score") or 0.0)
        ctype = payload.get("chunk_type")

        if ctype == "cell":
            row_idx = int(payload.get("row_index", -1))
            if row_idx >= 0:
                row_scores[(file, row_idx)] = row_scores.get((file, row_idx), 0.0) + score
        elif ctype == "row_window":
            start = int(payload.get("row_start", -1))
            end = int(payload.get("row_end", -1))
            if start >= 0 and end >= start:
                # Distribute the window score across its rows (simple heuristic)
                length = max(1, (end - start + 1))
                per_row = score / float(length)
                for r in range(start, end + 1):
                    row_scores[(file, r)] = row_scores.get((file, r), 0.0) + per_row

    # Get a broader preliminary ranking to support expansion heuristics
    prelim_ranked: List[Tuple[Tuple[str, int], float]] = sorted(
        row_scores.items(), key=lambda x: x[1], reverse=True
    )[: max(k * 2, 20)]

    # Load each file once
    df_cache: Dict[str, pd.DataFrame] = {}
    for (file, _), _s in prelim_ranked:
        if file not in df_cache:
            try:
                df_cache[file] = _load_df_for_file(file)
            except Exception:
                pass

    # Heuristic: detect a dominant person name and target year from the query,
    # then include all rows for that person (and year, if present) at the top.
    chosen_file: Optional[str] = prelim_ranked[0][0][0] if prelim_ranked else None
    chosen_row: Optional[int] = prelim_ranked[0][0][1] if prelim_ranked else None
    chosen_name: Optional[str] = None
    query_year: Optional[str] = None
    query_month: Optional[str] = None  # YYYY-MM
    query_date: Optional[str] = None   # YYYY-MM-DD

    # Extract date/month/year tokens if present
    import re
    m_date = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", str(text))
    if m_date:
        query_date = m_date.group(1)
    m_month = re.search(r"\b(\d{4}-\d{2})\b", str(text))
    if m_month:
        query_month = m_month.group(1)
        query_year = query_month.split("-")[0]
    else:
        # Fallback year-only
        for token in str(text).replace("?", " ").split():
            if token.isdigit() and len(token) == 4:
                query_year = token
                break

    if chosen_file and chosen_file in df_cache and chosen_row is not None:
        df0 = df_cache[chosen_file]
        if 0 <= chosen_row < len(df0) and "name" in df0.columns:
            try:
                chosen_name = str(df0.iloc[chosen_row]["name"]).strip()
            except Exception:
                chosen_name = None

    expanded_rows: List[Tuple[str, int]] = []
    if chosen_file and chosen_name and chosen_file in df_cache:
        df = df_cache[chosen_file]
        try:
            for idx in range(len(df)):
                try:
                    if str(df.iloc[idx].get("name", "")).strip() == chosen_name:
                        # Match by exact date if present
                        if query_date and "payment_date" in df.columns:
                            if str(df.iloc[idx]["payment_date"]) != query_date:
                                continue
                        # Else match by month if present
                        if not query_date and query_month and "competency" in df.columns:
                            comp = str(df.iloc[idx]["competency"])  # e.g., 2025-06
                            if not comp.startswith(query_month):
                                continue
                        # Else match by year if present
                        if not query_date and not query_month and query_year and "competency" in df.columns:
                            comp = str(df.iloc[idx]["competency"])  # e.g., 2025-03
                            if not comp.startswith(query_year):
                                continue
                        expanded_rows.append((chosen_file, idx))
                except Exception:
                    continue
        except Exception:
            expanded_rows = []

    # Preserve chronological order if competency exists
    if chosen_file and chosen_file in df_cache and "competency" in df_cache[chosen_file].columns:
        df = df_cache[chosen_file]
        try:
            expanded_rows.sort(key=lambda t: str(df.iloc[t[1]]["competency"]))
        except Exception:
            pass

    # If no chosen_name but we have a specific date, include all rows matching the date in any cached file
    if not chosen_name and query_date:
        for file, df in df_cache.items():
            if "payment_date" in df.columns:
                for idx in range(len(df)):
                    try:
                        if str(df.iloc[idx]["payment_date"]) == query_date:
                            expanded_rows.append((file, idx))
                    except Exception:
                        continue

    # Merge expansions at the top, then the preliminary ranking, deduplicated
    seen: set[Tuple[str, int]] = set()
    ordered: List[Tuple[Tuple[str, int], float]] = []
    for pair in expanded_rows:
        if pair not in seen:
            seen.add(pair)
            # Boost expanded rows if they weren't scored (use high default)
            ordered.append((pair, row_scores.get(pair, 1e6)))
    for item in prelim_ranked:
        if item[0] not in seen:
            seen.add(item[0])
            ordered.append(item)

    # Format final results up to k
    results: List[Dict[str, Any]] = []
    for (file, row_idx), agg_score in ordered[:k]:
        df = df_cache.get(file)
        if df is None or row_idx < 0 or row_idx >= len(df):
            continue
        row_text = _format_row_with_header(df, row_idx)
        results.append({
            "file": file,
            "row_index": int(row_idx),
            "value": row_text,
            "score": float(agg_score),
        })

    return results
