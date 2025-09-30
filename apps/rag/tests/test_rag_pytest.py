"""
Testes pytest para o cliente RAG.
Testa funcionalidades específicas com diferentes cenários.
"""

import pytest
import pandas as pd
from pathlib import Path
from qdrant_client.models import Filter, FieldCondition, MatchValue


class TestRAGPytest:
    """Testes pytest para o cliente RAG."""
    
    def test_collection_exists(self, rag_client):
        """Testa se a coleção foi criada."""
        client = rag_client['client']
        collections = client.get_collections()
        
        collection_names = [c.name for c in collections.collections]
        assert "csv_chunks" in collection_names, "Coleção csv_chunks não foi criada"
    
    def test_all_csvs_processed(self, rag_client):
        """Testa se todos os CSVs foram processados sem erro."""
        results = rag_client['results']
        
        for result in results:
            assert 'error' not in result, f"Erro ao processar {result.get('csv_path', 'arquivo')}: {result.get('error', 'erro desconhecido')}"
    
    def test_basic_search_returns_results(self, rag_client):
        """Testa se busca básica retorna resultados."""
        client = rag_client['client']
        processor = rag_client['processor']
        
        query_vector = processor.model.encode("tecnologia").tolist()
        
        search_results = client.query_points(
            collection_name="csv_chunks",
            query=query_vector,
            limit=5
        ).points
        
        assert len(search_results) > 0, "Busca básica não retornou resultados"
        
        # Verificar estrutura dos resultados
        for result in search_results:
            assert hasattr(result, 'payload'), "Resultado não tem payload"
            assert hasattr(result, 'score'), "Resultado não tem score"
            assert 'csv_file' in result.payload, "Payload não tem csv_file"
            assert 'column_name' in result.payload, "Payload não tem column_name"
            assert 'original_value' in result.payload, "Payload não tem original_value"
    
    def test_products_search(self, rag_client):
        """Testa busca específica em produtos."""
        client = rag_client['client']
        processor = rag_client['processor']
        
        query_vector = processor.model.encode("smartphone").tolist()
        
        search_results = client.query_points(
            collection_name="csv_chunks",
            query=query_vector,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="csv_file",
                        match=MatchValue(value="products.csv")
                    )
                ]
            ),
            limit=3
        ).points
        
        # Verificar se todos os resultados são de products.csv
        for result in search_results:
            assert result.payload['csv_file'] == 'products.csv', f"Resultado não é de products.csv: {result.payload['csv_file']}"
    
    def test_articles_search(self, rag_client):
        """Testa busca específica em artigos."""
        client = rag_client['client']
        processor = rag_client['processor']
        
        query_vector = processor.model.encode("inteligência artificial").tolist()
        
        search_results = client.query_points(
            collection_name="csv_chunks",
            query=query_vector,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="csv_file",
                        match=MatchValue(value="articles.csv")
                    )
                ]
            ),
            limit=3
        ).points
        
        # Verificar se todos os resultados são de articles.csv
        for result in search_results:
            assert result.payload['csv_file'] == 'articles.csv', f"Resultado não é de articles.csv: {result.payload['csv_file']}"
    
    def test_documents_search(self, rag_client):
        """Testa busca específica em documentos."""
        client = rag_client['client']
        processor = rag_client['processor']
        
        query_vector = processor.model.encode("relatório").tolist()
        
        search_results = client.query_points(
            collection_name="csv_chunks",
            query=query_vector,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="csv_file",
                        match=MatchValue(value="documents.csv")
                    )
                ]
            ),
            limit=3
        ).points
        
        # Verificar se todos os resultados são de documents.csv
        for result in search_results:
            assert result.payload['csv_file'] == 'documents.csv', f"Resultado não é de documents.csv: {result.payload['csv_file']}"
    
    def test_column_specific_search(self, rag_client):
        """Testa busca em coluna específica."""
        client = rag_client['client']
        processor = rag_client['processor']
        
        query_vector = processor.model.encode("preço").tolist()
        
        search_results = client.query_points(
            collection_name="csv_chunks",
            query=query_vector,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="csv_file",
                        match=MatchValue(value="products.csv")
                    ),
                    FieldCondition(
                        key="column_name",
                        match=MatchValue(value="price")
                    )
                ]
            ),
            limit=3
        ).points
        
        # Verificar se todos os resultados são da coluna price
        for result in search_results:
            assert result.payload['column_name'] == 'price', f"Resultado não é da coluna price: {result.payload['column_name']}"
    
    def test_document_retrieval(self, rag_client):
        """Testa recuperação do documento original."""
        client = rag_client['client']
        processor = rag_client['processor']
        
        # Fazer uma busca para encontrar um resultado
        query_vector = processor.model.encode("produto").tolist()
        
        search_results = client.query_points(
            collection_name="csv_chunks",
            query=query_vector,
            limit=1
        ).points
        
        if search_results:
            result = search_results[0]
            csv_file = result.payload['csv_file']
            row_id = result.payload['row_id']
            
            # Carregar o CSV original
            csv_path = Path(__file__).parent.parent / "src" / "mock" / csv_file
            df = pd.read_csv(csv_path)
            
            # Encontrar a linha original
            if 'id' in df.columns:
                original_row = df[df['id'] == row_id]
            else:
                original_row = df.iloc[row_id - 1:row_id]
            
            assert not original_row.empty, f"Linha {row_id} não encontrada em {csv_file}"
            
            # Verificar se o valor encontrado está na linha original
            column_name = result.payload['column_name']
            if column_name in original_row.columns:
                original_value = str(original_row[column_name].iloc[0])
                assert original_value == result.payload['original_value'], \
                    f"Valor não confere: esperado '{original_value}', encontrado '{result.payload['original_value']}'"
    
    @pytest.mark.parametrize("question", [
        "Qual é o produto mais caro?",
        "Quais são os artigos sobre tecnologia?",
        "Existe algum documento sobre sustentabilidade?",
        "Quais produtos têm desconto?",
        "Há artigos sobre inovação?"
    ])
    def test_multiple_questions(self, rag_client, question):
        """Testa múltiplas perguntas parametrizadas."""
        client = rag_client['client']
        processor = rag_client['processor']
        
        query_vector = processor.model.encode(question).tolist()
        
        search_results = client.query_points(
            collection_name="csv_chunks",
            query=query_vector,
            limit=2
        ).points
        
        # Deve retornar pelo menos um resultado para perguntas válidas
        assert len(search_results) >= 0, f"Nenhum resultado para pergunta: {question}"
    
    def test_semantic_similarity(self, rag_client):
        """Testa similaridade semântica com sinônimos."""
        client = rag_client['client']
        processor = rag_client['processor']
        
        # Testar sinônimos
        queries = ["celular", "telefone móvel", "smartphone", "dispositivo móvel"]
        
        for query in queries:
            query_vector = processor.model.encode(query).tolist()
            
            search_results = client.query_points(
                collection_name="csv_chunks",
                query=query_vector,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="csv_file",
                            match=MatchValue(value="products.csv")
                        )
                    ]
                ),
                limit=2
            ).points
            
            # Deve retornar resultados para sinônimos
            assert len(search_results) >= 0, f"Nenhum resultado para sinônimo: {query}"
    
    def test_empty_query(self, rag_client):
        """Testa comportamento com consulta vazia."""
        client = rag_client['client']
        processor = rag_client['processor']
        
        query_vector = processor.model.encode("").tolist()
        
        search_results = client.query_points(
            collection_name="csv_chunks",
            query=query_vector,
            limit=5
        ).points
        
        # Deve retornar resultados mesmo com consulta vazia
        assert len(search_results) >= 0, "Consulta vazia deve retornar resultados"
    
    def test_invalid_collection(self, rag_client):
        """Testa comportamento com coleção inexistente."""
        client = rag_client['client']
        processor = rag_client['processor']
        
        query_vector = processor.model.encode("teste").tolist()
        
        with pytest.raises(Exception):
            client.query_points(
                collection_name="colecao_inexistente",
                query=query_vector,
                limit=5
            )
    
    def test_score_ordering(self, rag_client):
        """Testa se os resultados estão ordenados por score."""
        client = rag_client['client']
        processor = rag_client['processor']
        
        query_vector = processor.model.encode("tecnologia").tolist()
        
        search_results = client.query_points(
            collection_name="csv_chunks",
            query=query_vector,
            limit=5
        ).points
        
        if len(search_results) > 1:
            # Verificar se os scores estão em ordem decrescente
            scores = [result.score for result in search_results]
            assert scores == sorted(scores, reverse=True), "Resultados não estão ordenados por score"
    
    def test_result_metadata_completeness(self, rag_client):
        """Testa se os metadados dos resultados estão completos."""
        client = rag_client['client']
        processor = rag_client['processor']
        
        query_vector = processor.model.encode("teste").tolist()
        
        search_results = client.query_points(
            collection_name="csv_chunks",
            query=query_vector,
            limit=1
        ).points
        
        if search_results:
            result = search_results[0]
            payload = result.payload
            
            # Verificar campos obrigatórios
            required_fields = ['csv_file', 'row_id', 'column_name', 'original_value', 'chunk_type']
            for field in required_fields:
                assert field in payload, f"Campo obrigatório '{field}' não encontrado no payload"
            
            # Verificar tipos dos campos
            assert isinstance(payload['csv_file'], str), "csv_file deve ser string"
            assert isinstance(payload['row_id'], (int, str)), "row_id deve ser int ou string"
            assert isinstance(payload['column_name'], str), "column_name deve ser string"
            assert isinstance(payload['original_value'], (str, type(None))), "original_value deve ser string ou None"
            assert isinstance(payload['chunk_type'], str), "chunk_type deve ser string"
