# Desafio Capgemini

Monorepo built with Nx containing:

- UI: Next.js 15 + React 19 + TailwindCSS (`apps/ui`)
- AI API: FastAPI (Python 3.12+) (`apps/ai`)

## Project structure

```
apps/
  ui/   # Next.js frontend (API route proxies to AI)
  ai/   # FastAPI backend (LLM agent)
```

## Prerequisites

- Node.js 20+ and pnpm
- Python 3.12+

## Quick start

1) Install dependencies at the repo root:

```bash
pnpm install
```

2) Configure environment variables.

- UI (`apps/ui`): create `.env.local` with:

```env
# Optional. Override AI endpoint used by /api/ai route
AI_API=http://localhost:8000/ai/generate
```

- AI (`apps/ai`): create `.env` (if needed) and ensure Python 3.12 is active.

3) Run both apps in development:

Terminal A (AI API):

```bash
cd apps/ai
pip install uv
uv sync
uv run python main.py
```

Terminal B (UI):

```bash
cd apps/ui
pnpm dev
```

The UI will be at `http://localhost:3000` and calls the AI API at `http://localhost:8000/ai/generate` (or the value from `AI_API`).

## How it works

- The UI sends POST `/api/ai` with `{ message: string }`.
- The Next.js route at `apps/ui/src/app/api/ai/route.ts` forwards to `AI_API` (default `http://localhost:8000/ai/generate`).
- The FastAPI app at `apps/ai/main.py` exposes:
  - `GET /ai/health/`
  - `POST /ai/generate/` → returns `{ message: string }` from the agent.

## Scripts

- UI (`apps/ui`):
  - `pnpm dev` — start Next.js with Turbopack
  - `pnpm build` — build production
  - `pnpm start` — start production server
  - `pnpm lint` — run eslint

- AI (`apps/ai`): managed via `uv` and `pyproject.toml`:
  - `uv sync` — install Python deps
  - `uv run python main.py` — run FastAPI locally (port 8000 by default)

## Tech

- Nx workspace at the root to organize projects
- Next.js 15, React 19, TailwindCSS for the UI
- FastAPI, LangChain/Graph for the AI agent

## Deployment notes

- UI can be deployed to any Next.js-compatible host.
- AI can be deployed as a standard FastAPI service (e.g., Uvicorn/Gunicorn).
- Ensure `AI_API` in the UI environment points to the deployed AI endpoint.

## License

MIT
