import pytest
import sys
import os
from pathlib import Path

# Adicionar o diretório src ao path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)


@pytest.fixture(scope="session")
def rag_client():
    """Fixture que fornece um cliente RAG configurado para os testes."""
    import sys, os
    # Ensure src is importable when running from apps/rag
    src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    from csv_chunk_processor import process_csvs_as_chunks
    from csv_chunk_processor import CSVChunkProcessor
    
    # Processar CSVs reais em src/archives
    # Use a fresh client/path per session to avoid concurrent access issues
    from qdrant_client import QdrantClient
    import tempfile
    tmp_dir = tempfile.mkdtemp(prefix="qdrant-db-")
    client = QdrantClient(path=tmp_dir)
    results, client = process_csvs_as_chunks(client=client)
    processor = CSVChunkProcessor()
    
    return {
        'client': client,
        'processor': processor,
        'results': results
    }


@pytest.fixture
def sample_questions():
    """Fixture com perguntas de exemplo para testes."""
    return [
        "Qual é o produto mais caro?",
        "Quais são os artigos sobre tecnologia?",
        "Existe algum documento sobre sustentabilidade?",
        "Quais produtos têm desconto?",
        "Há artigos sobre inovação?",
        "Qual o preço do smartphone?",
        "Quais são os títulos dos artigos?",
        "Existe algum relatório sobre IA?",
        "Quais produtos estão em promoção?",
        "Há documentos sobre blockchain?"
    ]
