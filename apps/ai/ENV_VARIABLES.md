# Variáveis de Ambiente - Serviço AI

## Configuração do Serviço RAG

As seguintes variáveis de ambiente devem ser configuradas para que o serviço AI possa acessar o serviço RAG:

### Obrigatórias

- `RAG_SERVICE_HOST`: Nome do host do serviço RAG (padrão: `localhost`)
- `RAG_SERVICE_PORT`: Porta do serviço RAG (padrão: `8080`)
- `RAG_SERVICE_PROTOCOL`: Protocolo de comunicação (padrão: `http`)

### Opcionais

- `RAG_TIMEOUT`: Timeout para requisições em segundos (padrão: `30`)

## Exemplo de Configuração

### Docker Compose
```yaml
services:
  ai:
    environment:
      - RAG_SERVICE_HOST=rag
      - RAG_SERVICE_PORT=8080
      - RAG_SERVICE_PROTOCOL=http
      - RAG_TIMEOUT=30
    depends_on:
      - rag
  
  rag:
    # configuração do serviço RAG
```

### Arquivo .env
```bash
RAG_SERVICE_HOST=rag
RAG_SERVICE_PORT=8080
RAG_SERVICE_PROTOCOL=http
RAG_TIMEOUT=30
```

## Uso das Ferramentas

```python
from src.tools.rag import get_rag_tools, create_rag_agent_tools

# Obter lista de ferramentas
tools = get_rag_tools()

# Ou obter dicionário para agentes
tool_dict = create_rag_agent_tools()
```
