# Desafio Capgemini – AI + RAG + UI

Monorepo com três aplicações:
- apps/rag: Serviço RAG (FastAPI) para indexação e busca semântica em CSVs
- apps/ai: Serviço de agente (FastAPI) com ReAct e ferramentas (RAG e busca web)
- apps/ui: Frontend Next.js com chat e aba para executar testes


## Pré‑requisitos
- Node.js 20+ e pnpm 9+
- Python 3.12+ e [uv](https://docs.astral.sh/uv/)
- (Opcional) [Ollama](https://ollama.ai) com modelo `qwen3:latest`


## Setup
1) Instalar dependências (raiz)
```bash
pnpm install
```

2) Instalar dependências Python
```bash
uv sync -C apps/rag
uv sync -C apps/ai
```

3) Variáveis de ambiente (defaults razoáveis)
- apps/rag: `RAG_PORT` (8080)
- apps/ai: `AI_PORT` (8000), `RAG_SERVICE_URL` (http://localhost:8080), `RAG_TIMEOUT` (30)
- apps/ui: `AI_API` (http://localhost:8000/ai/generate)


### Formato dos arquivos .env

apps/ai/.env
```
AI_PORT=8000
RAG_SERVICE_URL=http://localhost:8080
RAG_TIMEOUT=30
# OLLAMA_HOST=http://localhost:11434
```

apps/rag/.env
```
RAG_PORT=8080
# EMBEDDING_MODEL=all-MiniLM-L6-v2
# CROSS_ENCODER=cross-encoder/ms-marco-MiniLM-L-6-v2
```

apps/ui/.env.local
```
AI_API=http://localhost:8000/ai/generate
```


## Como rodar
RAG (ingestão + API)
```bash
uv run -C apps/rag python main.py
# http://localhost:8080
```

AI (agente ReAct + ferramentas)
```bash
uv run -C apps/ai python main.py
# http://localhost:8000
```

UI (Next.js)
```bash
pnpm --dir apps/ui dev
# http://localhost:3000
```

Observação: `apps/ui/src/app/api/ai/route.ts` faz proxy para `AI_API`.


## Como funciona
- A UI envia POST `/api/ai` com `{ message }` → proxy para `/ai/generate/` (AI)
- O serviço AI usa um agente ReAct (LangGraph) com ferramentas:
  - `search_rag`: consulta o serviço RAG e retorna linhas e fontes
  - `web_search`: fallback quando RAG é insuficiente
- O serviço RAG indexa CSVs com chunks de célula e janelas de linhas, permitindo busca semântica por linha inteira (com cabeçalho) e suporte a consultas por data/compentência.


## Testes
Via UI (Aba “Teste”): botões para RAG, AI, UI ou todos.

Terminal:
```bash
# RAG
uv run -C apps/rag pytest -vv

# AI
uv run -C apps/ai pytest -vv

# UI
pnpm --dir apps/ui test
```

Aviso:
- Os testes do RAG usam Qdrant em modo local (arquivo). Não execute os testes com o serviço RAG rodando em background, pois há lock de concorrência no diretório de storage. Pare o serviço RAG antes de rodar `pytest` ou execute em ambiente isolado.


## Decisões técnicas
- Agente (apps/ai)
  - LangChain/LangGraph: ecossistema amplamente utilizado, documentação extensa e integrações maduras; o prebuilt `create_react_agent` reduz complexidade de orquestração.
  - Arquitetura ReAct: maior acurácia e eficiência no uso de ferramentas (melhor explicabilidade, menos chamadas desnecessárias).
  - LLM via Ollama (`qwen3:latest`), temperatura 0.
  - Prompt: RAG primeiro; se insuficiente, web; citar fontes ao usar ferramentas.
- RAG (apps/rag)
  - Qdrant Local: base vetorial open‑source, roda localmente com boa acurácia e sem dependências externas.
  - Indexação dupla: célula (precisão) + janelas de linhas (recall/contexto); cada chunk traz cabeçalho do CSV.
  - Busca semântica com SentenceTransformers; re‑ranking opcional por CrossEncoder.
  - Heurísticas de expansão por nome e por ano/mês/data (e.g. `2025-06-28`).
- UI (apps/ui)
  - Next.js + Tailwind para produtividade/UX.
  - Monorepo Nx: facilita integração de UI/AI/RAG, compartilhamento de scripts e execução de testes a partir de um único repositório.


## Limitações
- Qdrant Local usa lock de arquivo; em execução concorrente prefira Qdrant server/Cloud (nos testes usamos diretórios temporários).
- Qualidade da resposta depende do modelo local do Ollama e do contexto recuperado.
- Web search não é autenticada; recomenda‑se pós‑validação das fontes.
- CSVs muito grandes podem demandar infra de vetor DB dedicada.

Maior limitação atual:
- Busca do RAG (recall/precisão). Em cenários específicos, recomenda‑se re‑indexação, ajuste de `k/prefetch` e re‑ranking; para produção, avaliar Qdrant server.


## Roadmap curto
- Contêinerização com Docker (UI/AI/RAG) e `docker-compose` para orquestração local
- Ajustes de observabilidade do agente (trace de ferramentas)
- Estratégias de re‑ranking e normalização de scores
- Upload de CSVs pela UI
- Erro de import em testes Python: rode `uv sync -C apps/<svc>` e selecione a venv correta.
- Lock do Qdrant: finalize processos concorrentes; os testes já isolam com diretórios temporários.
- UI não chama AI: ajuste `AI_API` ou suba o serviço AI em `http://localhost:8000`.
- Ollama: confirme que o servidor está ativo e o modelo `qwen3:latest` foi baixado.

