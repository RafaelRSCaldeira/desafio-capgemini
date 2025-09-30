# Sistema RAG com Qdrant

Este projeto implementa um sistema de Retrieval-Augmented Generation (RAG) usando Qdrant como banco de dados vetorial para armazenar e buscar embeddings de documentos.

## Funcionalidades

- **Processamento de CSVs**: Converte arquivos CSV em embeddings usando modelos de linguagem
- **Indexação no Qdrant**: Armazena embeddings em coleções organizadas no Qdrant
- **Busca semântica**: Realiza buscas por similaridade usando embeddings
- **Filtros avançados**: Suporte a filtros por metadados durante a busca

## Estrutura do Projeto

```
src/
├── qdrant/
│   ├── client.py          # Cliente Qdrant principal
│   └── qdrant_db/         # Diretório para persistência (opcional)
├── mock/                  # Arquivos CSV de exemplo
│   ├── products.csv       # Produtos com descrições
│   ├── documents.csv      # Documentos técnicos
│   └── articles.csv       # Artigos e notícias
└── csv_processor.py       # Processador de CSVs e embeddings
```

## Dependências

- `qdrant-client`: Cliente para o banco de dados vetorial Qdrant
- `sentence-transformers`: Modelos para geração de embeddings
- `pandas`: Processamento de dados CSV
- `numpy`: Operações numéricas

## Como Usar

### 1. Instalar Dependências

```bash
cd apps/rag
pip install -e .
```

### 2. Executar Teste Completo

```bash
python src/qdrant/client.py
```

Este comando irá:
- Processar todos os CSVs mock
- Criar coleções no Qdrant
- Gerar embeddings usando o modelo `all-MiniLM-L6-v2`
- Realizar buscas de exemplo
- Mostrar resultados das buscas

### 3. Processar CSVs Personalizados

```python
from csv_processor import CSVProcessor
from qdrant_client import QdrantClient

# Inicializar processador
processor = CSVProcessor()

# Conectar ao Qdrant
client = QdrantClient(":memory:")  # ou URL do servidor

# Processar CSV
result = processor.process_csv_to_qdrant(
    csv_path="caminho/para/seu/arquivo.csv",
    collection_name="minha_colecao",
    text_columns=["titulo", "conteudo", "tags"],  # Colunas para embedding
    id_column="id",
    client=client
)
```

### 4. Realizar Buscas

```python
# Buscar documentos similares
query_vector = processor.model.encode("sua consulta aqui").tolist()

results = client.search(
    collection_name="minha_colecao",
    query_vector=query_vector,
    limit=5
)

for result in results:
    print(f"Score: {result.score}")
    print(f"Dados: {result.payload}")
```

## Arquivos CSV Mock

### products.csv
Contém produtos eletrônicos com:
- Nome, descrição, categoria
- Preço, avaliação, características
- Colunas para embedding: `name`, `description`, `features`

### documents.csv
Contém documentos técnicos com:
- Título, conteúdo, categoria
- Autor, data, palavras-chave
- Colunas para embedding: `title`, `content`, `keywords`

### articles.csv
Contém artigos e notícias com:
- Título, resumo, conteúdo
- Autor, data de publicação, tags
- Colunas para embedding: `title`, `summary`, `content`, `tags`

## Configurações

### Modelo de Embedding
Por padrão, usa `all-MiniLM-L6-v2` (384 dimensões). Para alterar:

```python
processor = CSVProcessor(model_name="outro-modelo")
```

### Métricas de Distância
O Qdrant usa distância cosseno por padrão. Outras opções:
- `Distance.COSINE`: Cosseno (padrão)
- `Distance.EUCLIDEAN`: Euclidiana
- `Distance.DOT`: Produto escalar

## Exemplos de Busca

### Busca Simples
```python
# Buscar produtos similares a "smartphone"
query = "smartphone com boa câmera"
results = client.search(collection_name="products", query_vector=...)
```

### Busca com Filtros
```python
# Buscar produtos com preço menor que 1000
results = client.search(
    collection_name="products",
    query_vector=...,
    query_filter={
        "must": [{"key": "price", "range": {"lt": 1000}}]
    }
)
```

### Busca por Categoria
```python
# Buscar apenas documentos de tecnologia
results = client.search(
    collection_name="documents",
    query_vector=...,
    query_filter={
        "must": [{"key": "category", "match": {"value": "Tecnologia"}}]
    }
)
```

## Próximos Passos

- [ ] Integração com API REST (FastAPI)
- [ ] Interface web para busca
- [ ] Suporte a mais formatos de arquivo
- [ ] Otimizações de performance
- [ ] Persistência em disco
- [ ] Configurações avançadas de embedding
