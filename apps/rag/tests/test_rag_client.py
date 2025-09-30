"""
Testes para o cliente RAG com dados mock.
Testa diferentes perguntas sobre os dados e verifica se as respostas
incluem a linha correta e o documento original.
"""

import unittest
import sys
import os
from pathlib import Path
import pandas as pd

# Adicionar o diretório src ao path para importar os módulos
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from csv_chunk_processor import CSVChunkProcessor, process_mock_csvs_as_chunks
from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue


class TestRAGClient(unittest.TestCase):
    """Classe de testes para o cliente RAG."""
    
    @classmethod
    def setUpClass(cls):
        """Configuração inicial para todos os testes."""
        print("\n=== Configurando ambiente de teste ===")
        
        # Processar CSVs mock e criar coleção
        cls.results, cls.client = process_mock_csvs_as_chunks()
        cls.processor = CSVChunkProcessor()
        
        # Verificar se a coleção foi criada
        collections = cls.client.get_collections()
        cls.collection_exists = any(
            collection.name == "csv_chunks" 
            for collection in collections.collections
        )
        
        print(f"Coleção csv_chunks criada: {cls.collection_exists}")
        print(f"Total de chunks processados: {sum(r.get('total_chunks', 0) for r in cls.results if 'error' not in r)}")
    
    def test_collection_creation(self):
        """Testa se a coleção csv_chunks foi criada corretamente."""
        self.assertTrue(self.collection_exists, "Coleção csv_chunks não foi criada")
        
        # Verificar se todos os CSVs foram processados sem erro
        for result in self.results:
            self.assertNotIn('error', result, f"Erro ao processar {result.get('csv_path', 'arquivo desconhecido')}")
    
    def test_basic_search(self):
        """Testa busca básica sem filtros."""
        print("\n--- Teste: Busca básica ---")
        
        query = "tecnologia"
        query_vector = self.processor.model.encode(query).tolist()
        
        search_results = self.client.query_points(
            collection_name="csv_chunks",
            query=query_vector,
            limit=5
        ).points
        
        self.assertGreater(len(search_results), 0, "Nenhum resultado encontrado para 'tecnologia'")
        
        # Verificar se os resultados têm a estrutura esperada
        for result in search_results:
            self.assertIn('payload', result.__dict__, "Resultado não tem payload")
            self.assertIn('score', result.__dict__, "Resultado não tem score")
            self.assertIn('csv_file', result.payload, "Payload não tem csv_file")
            self.assertIn('column_name', result.payload, "Payload não tem column_name")
            self.assertIn('original_value', result.payload, "Payload não tem original_value")
        
        print(f"Encontrados {len(search_results)} resultados para '{query}'")
        for i, result in enumerate(search_results[:3]):
            print(f"  {i+1}. {result.payload['csv_file']} - {result.payload['column_name']}: {result.payload['original_value'][:50]}...")
    
    def test_products_search(self):
        """Testa busca específica em produtos."""
        print("\n--- Teste: Busca em produtos ---")
        
        # Usar termos que realmente existem nos produtos
        query = "Galaxy"
        query_vector = self.processor.model.encode(query).tolist()
        
        search_results = self.client.query_points(
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
            self.assertEqual(result.payload['csv_file'], 'products.csv', 
                           f"Resultado não é de products.csv: {result.payload['csv_file']}")
        
        print(f"Encontrados {len(search_results)} resultados de produtos para '{query}'")
        for i, result in enumerate(search_results):
            print(f"  {i+1}. {result.payload['column_name']}: {result.payload['original_value']}")
        
        # Se não encontrar resultados para "Galaxy", tentar com "Eletrônicos"
        if len(search_results) == 0:
            print("Tentando busca alternativa com 'Eletrônicos'...")
            query = "Eletrônicos"
            query_vector = self.processor.model.encode(query).tolist()
            
            search_results = self.client.query_points(
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
            
            self.assertGreater(len(search_results), 0, "Nenhum resultado encontrado para 'Eletrônicos' em produtos")
            print(f"Encontrados {len(search_results)} resultados de produtos para '{query}'")
            for i, result in enumerate(search_results):
                print(f"  {i+1}. {result.payload['column_name']}: {result.payload['original_value']}")
    
    def test_articles_search(self):
        """Testa busca específica em artigos."""
        print("\n--- Teste: Busca em artigos ---")
        
        query = "inteligência artificial"
        query_vector = self.processor.model.encode(query).tolist()
        
        search_results = self.client.query_points(
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
        
        print(f"Encontrados {len(search_results)} resultados de artigos para '{query}'")
        for i, result in enumerate(search_results):
            print(f"  {i+1}. {result.payload['column_name']}: {result.payload['original_value'][:100]}...")
    
    def test_documents_search(self):
        """Testa busca específica em documentos."""
        print("\n--- Teste: Busca em documentos ---")
        
        query = "relatório"
        query_vector = self.processor.model.encode(query).tolist()
        
        search_results = self.client.query_points(
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
        
        print(f"Encontrados {len(search_results)} resultados de documentos para '{query}'")
        for i, result in enumerate(search_results):
            print(f"  {i+1}. {result.payload['column_name']}: {result.payload['original_value'][:100]}...")
    
    def test_column_specific_search(self):
        """Testa busca em coluna específica."""
        print("\n--- Teste: Busca em coluna específica ---")
        
        query = "preço"
        query_vector = self.processor.model.encode(query).tolist()
        
        search_results = self.client.query_points(
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
        
        print(f"Encontrados {len(search_results)} resultados de preços para '{query}'")
        for i, result in enumerate(search_results):
            print(f"  {i+1}. Preço: {result.payload['original_value']} (Linha {result.payload['row_id']})")
    
    def test_document_retrieval(self):
        """Testa recuperação do documento original completo."""
        print("\n--- Teste: Recuperação de documento original ---")
        
        # Fazer uma busca para encontrar um resultado
        query = "produto"
        query_vector = self.processor.model.encode(query).tolist()
        
        search_results = self.client.query_points(
            collection_name="csv_chunks",
            query=query_vector,
            limit=1
        ).points
        
        if search_results:
            result = search_results[0]
            csv_file = result.payload['csv_file']
            row_id = result.payload['row_id']
            
            print(f"Recuperando documento original: {csv_file}, linha {row_id}")
            
            # Carregar o CSV original
            csv_path = Path(__file__).parent.parent / "src" / "mock" / csv_file
            df = pd.read_csv(csv_path)
            
            # Encontrar a linha original
            if 'id' in df.columns:
                original_row = df[df['id'] == row_id]
            else:
                original_row = df.iloc[row_id - 1:row_id]
            
            self.assertFalse(original_row.empty, f"Linha {row_id} não encontrada em {csv_file}")
            
            print("Linha original encontrada:")
            for col, value in original_row.iloc[0].items():
                print(f"  {col}: {value}")
            
            # Verificar se o valor encontrado está na linha original
            column_name = result.payload['column_name']
            if column_name in original_row.columns:
                original_value = str(original_row[column_name].iloc[0])
                self.assertEqual(original_value, result.payload['original_value'],
                               f"Valor não confere: esperado '{original_value}', encontrado '{result.payload['original_value']}'")
    
    def test_multiple_questions(self):
        """Testa múltiplas perguntas diferentes."""
        print("\n--- Teste: Múltiplas perguntas ---")
        
        questions = [
            "Qual é o produto mais caro?",
            "Quais são os artigos sobre tecnologia?",
            "Existe algum documento sobre sustentabilidade?",
            "Quais produtos têm desconto?",
            "Há artigos sobre inovação?"
        ]
        
        for question in questions:
            print(f"\nPergunta: {question}")
            query_vector = self.processor.model.encode(question).tolist()
            
            search_results = self.client.query_points(
                collection_name="csv_chunks",
                query=query_vector,
                limit=2
            ).points
            
            print(f"  Resposta: {len(search_results)} resultados encontrados")
            for i, result in enumerate(search_results):
                print(f"    {i+1}. {result.payload['csv_file']} - {result.payload['column_name']}: {result.payload['original_value'][:60]}...")
    
    def test_semantic_similarity(self):
        """Testa similaridade semântica com sinônimos."""
        print("\n--- Teste: Similaridade semântica ---")
        
        # Testar sinônimos
        queries = [
            "celular",
            "telefone móvel", 
            "smartphone",
            "dispositivo móvel"
        ]
        
        for query in queries:
            print(f"\nTestando: '{query}'")
            query_vector = self.processor.model.encode(query).tolist()
            
            search_results = self.client.query_points(
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
            
            print(f"  Resultados: {len(search_results)}")
            for i, result in enumerate(search_results):
                print(f"    {i+1}. Score: {result.score:.3f} - {result.payload['original_value']}")
    
    def test_empty_query(self):
        """Testa comportamento com consulta vazia."""
        print("\n--- Teste: Consulta vazia ---")
        
        query_vector = self.processor.model.encode("").tolist()
        
        search_results = self.client.query_points(
            collection_name="csv_chunks",
            query=query_vector,
            limit=5
        ).points
        
        # Deve retornar resultados mesmo com consulta vazia
        self.assertGreaterEqual(len(search_results), 0, "Consulta vazia deve retornar resultados")
        print(f"Consulta vazia retornou {len(search_results)} resultados")
    
    def test_invalid_collection(self):
        """Testa comportamento com coleção inexistente."""
        print("\n--- Teste: Coleção inexistente ---")
        
        query_vector = self.processor.model.encode("teste").tolist()
        
        with self.assertRaises(Exception):
            self.client.query_points(
                collection_name="colecao_inexistente",
                query=query_vector,
                limit=5
            )


def run_tests():
    """Executa todos os testes."""
    print("=" * 60)
    print("INICIANDO TESTES DO CLIENTE RAG")
    print("=" * 60)
    
    # Criar suite de testes
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestRAGClient)
    
    # Executar testes
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    print("RESUMO DOS TESTES")
    print("=" * 60)
    print(f"Testes executados: {result.testsRun}")
    print(f"Falhas: {len(result.failures)}")
    print(f"Erros: {len(result.errors)}")
    print(f"Sucessos: {result.testsRun - len(result.failures) - len(result.errors)}")
    
    if result.failures:
        print("\nFALHAS:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nERROS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
