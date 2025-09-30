from fastapi import FastAPI, HTTPException
import uvicorn
from dotenv import load_dotenv
import os
from pydantic import BaseModel
import sys

from src.csv_chunk_processor import process_csvs_as_chunks, find_top_k_rows

app = FastAPI()

class SimilarRequest(BaseModel):
    text: str
    k: int | None = 10

_rag_client = None

@app.get("/rag/health/")
def health():
    return {"status": 201}

@app.post("/rag/similar")
def similar(req: SimilarRequest):
    global _rag_client
    if not req.text or not isinstance(req.text, str):
        raise HTTPException(status_code=400, detail="'text' must be a non-empty string")
    if _rag_client is None:
        _, _rag_client = process_csvs_as_chunks()
    # Use row-level semantic search that returns full rows with headers
    topk = find_top_k_rows(req.text, _rag_client, k=10)
    # Map to backward-compatible schema expected by the AI app
    results = []
    for item in topk:
        results.append({
            "value": item.get("value"),
            "file": item.get("file"),
            "score": item.get("score"),
        })
    print(results)
    return {"results": results}

if __name__ == "__main__":
    load_dotenv()
    PORT = int(os.getenv("RAG_PORT", 8080))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT
    )