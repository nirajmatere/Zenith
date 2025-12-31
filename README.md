# Zenith (Monorepo)

AI-first B2B assessment + learning platform for JEE/NEET institutes.

## Repo layout
- `apps/api` — FastAPI backend (Postgres + Redis + Celery)
- `apps/web` — Next.js frontend (NTA-style exam UI)
- `docs` — engineering rules (DEVOS), architecture decisions (ADR)
- `infra/docker` — local dev docker-compose

## Quick start (local)
### 1) Prereqs
- Docker + Docker Compose
- Python 3.12+
- Node 20+ + pnpm

### 2) Start Postgres + Redis
```bash
docker compose -f infra/docker/docker-compose.yml up -d
```

### 3) Backend
```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
uvicorn zenith_api.main:app --reload --port 8000
```

### 4) Frontend
```bash
cd apps/web
pnpm install
pnpm dev
```

### URLs
- API: http://localhost:8000/health
- API docs (OpenAPI): http://localhost:8000/docs
- Web: http://localhost:3000
