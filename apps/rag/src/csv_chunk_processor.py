import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct


class CSVChunkProcessor:    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
    
    def create_chunk_text(self, value: Any, column_name: str) -> str:
        if pd.isna(value):
            return f"{column_name}: [valor não disponível]"
        return f"{column_name}: {str(value)}"
    
    def create_chunks_from_csv(
        self, 
        df: pd.DataFrame, 
        csv_filename: str,
        start_chunk_id: int = 1,
        id_column: str = "id"
    ) -> List[Dict[str, Any]]:
        chunks = []
        chunk_id = start_chunk_id
        
        for row_idx, row in df.iterrows():
            # Obter ID da linha se existir
            row_id = row[id_column] if id_column in row else row_idx + 1
            
            for col_name, value in row.items():
                # Pular a coluna ID para evitar duplicação
                if col_name == id_column:
                    continue
                    
                # Criar texto do chunk
                chunk_text = self.create_chunk_text(value, col_name)
                
                # Criar metadados
                metadata = {
                    "csv_file": csv_filename,
                    "row_id": row_id,
                    "column_name": col_name,
                    "row_index": row_idx,
                    "original_value": str(value) if not pd.isna(value) else None,
                    "chunk_type": "csv_cell"
                }
                
                chunks.append({
                    "id": chunk_id,
                    "text": chunk_text,
                    "metadata": metadata
                })
                
                chunk_id += 1
        
        return chunks
    
    def generate_embeddings_for_chunks(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        texts = [chunk["text"] for chunk in chunks]
        embeddings = self.model.encode(texts)
        
        for i, chunk in enumerate(chunks):
            chunk["embedding"] = embeddings[i].tolist()
        
        return chunks
    
    def create_qdrant_points(self, chunks: List[Dict[str, Any]]) -> List[PointStruct]:
        points = []
        
        for chunk in chunks:
            points.append(PointStruct(
                id=chunk["id"],
                vector=chunk["embedding"],
                payload=chunk["metadata"]
            ))
        
        return points
    
    def process_csv_to_qdrant_chunks(
        self,
        csv_path: str,
        collection_name: str,
        client: Optional[QdrantClient] = None,
        start_chunk_id: int = 1
    ) -> Dict[str, Any]:
        if client is None:
            client = QdrantClient(path=Path(__file__).parent / "db")
        
        # Carregar CSV
        df = pd.read_csv(csv_path)
        csv_filename = Path(csv_path).name
        
        # Criar coleção se não existir
        try:
            client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=self.embedding_dim,
                    distance=Distance.COSINE
                )
            )
        except Exception:
            # Coleção já existe
            pass
        
        # Criar chunks
        chunks = self.create_chunks_from_csv(df, csv_filename, start_chunk_id)
        
        # Gerar embeddings
        chunks_with_embeddings = self.generate_embeddings_for_chunks(chunks)
        
        # Criar pontos
        points = self.create_qdrant_points(chunks_with_embeddings)
        
        # Inserir no Qdrant
        client.upsert(
            collection_name=collection_name,
            points=points
        )
        
        return {
            "csv_path": csv_path,
            "csv_filename": csv_filename,
            "collection_name": collection_name,
            "total_chunks": len(points),
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "embedding_dimension": self.embedding_dim
        }


def process_csvs_as_chunks(csv_paths: List[str] = None, collection_name: str = "csv_chunks"):
    processor = CSVChunkProcessor()
    client = QdrantClient(path=Path(__file__).parent / "db")
    
    results = []
    global_chunk_id = 1  # ID global para evitar sobreposição
    
    import os

    if csv_paths is None:
        csv_folder = os.path.join(os.path.dirname(__file__), "archives")
        csv_paths = [os.path.join(csv_folder, file) for file in os.listdir(csv_folder)]

        
    print(csv_paths)
        
    for csv_path in csv_paths:
        try:
            print(f"[PROC] Processando {csv_path} como chunks...")
            
            result = processor.process_csv_to_qdrant_chunks(
                csv_path=csv_path,
                collection_name=collection_name,
                client=client,
                start_chunk_id=global_chunk_id
            )
            
            results.append(result)
            global_chunk_id += result['total_chunks']  # Atualizar ID global
            
            print(f"[OK] {csv_path} processado: {result['total_chunks']} chunks criados")
            print(f"   [INFO] {result['total_rows']} linhas × {result['total_columns']} colunas")
            
        except Exception as e:
            print(f"[ERRO] Erro ao processar {csv_path}: {e}")
            results.append({
                "csv_path": csv_path,
                "error": str(e)
            })
    
    return results, client


def find_top_k_similar(
    text: str,
    client: QdrantClient,
    k: int = 3,
    collection_name: str = "csv_chunks"
):
    processor = CSVChunkProcessor()
    query_vector = processor.model.encode(text).tolist()
    results = client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=max(1, k)
    ).points
    top = []
    for r in results:
        payload = r.payload or {}
        top.append({
            "value": payload.get("original_value"),
            "file": payload.get("csv_file")
        })
    return top
