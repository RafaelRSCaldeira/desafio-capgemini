from fastapi import FastAPI, HTTPException
import uvicorn
from dotenv import load_dotenv
import os
from pydantic import BaseModel
import sys

from src.csv_chunk_processor import process_csvs_as_chunks, find_top_k_similar

app = FastAPI()

class SimilarRequest(BaseModel):
    text: str
    k: int | None = 3

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
        # Initialize in-memory qdrant and load mock CSVs
        _, _rag_client = process_csvs_as_chunks()
    topk = find_top_k_similar(req.text, _rag_client, k=req.k or 3)
    return {"results": topk}

if __name__ == "__main__":
    load_dotenv()
    PORT = int(os.getenv("RAG_PORT", 8080))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT
    )