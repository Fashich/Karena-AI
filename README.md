# Karena AI

**Enterprise RAG Knowledge Intelligence Platform**

by Ahmad Fashich Azzuhri Ramadhani

Karena AI unifies fragmented enterprise knowledge silos into a cloud-native retrieval-augmented generation (RAG) assistant with sub-second retrieval, source traceability, and production-grade observability for APAC regulated industries.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  React Frontend (Landing + Chat + Admin)                    │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST /api/v1
┌──────────────────────────▼──────────────────────────────────┐
│  FastAPI Gateway                                            │
│  ├── RAG Pipeline (hybrid retrieval → re-rank → generate)   │
│  ├── Agent Orchestrator (ADK-ready)                         │
│  ├── Memory Store (sessions, audit trail)                   │
│  └── Multi-tier Cache (memory + Redis)                      │
└──────┬─────────────────┬─────────────────┬──────────────────┘
       │                 │                 │
   Qdrant            Redis            SQLite/Postgres
 (vectors)          (cache)           (memory)
```

## Quick Start

### Prerequisites

- Python 3.11+ and Node.js 20+
- Docker Desktop **optional** (for Qdrant + Redis in production-like mode)

### Option A — No Docker (recommended if `docker compose` fails)

See **[docs/LOCAL_DEV_WITHOUT_DOCKER.md](docs/LOCAL_DEV_WITHOUT_DOCKER.md)**.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
mkdir data
python scripts\seed_knowledge.py
python run.py
```

Uses in-memory vectors + SQLite. No `docker compose` required.

### Option B — With Docker (Qdrant + Redis)

```bash
docker compose up -d qdrant redis
```

Set `VECTOR_STORE=qdrant` in `backend/.env`.

### Backend setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env
mkdir data
python scripts/seed_knowledge.py
python run.py
```

API: http://localhost:8000/docs

### 3. Frontend

```bash
cd app
npm install
npm run dev
```

- Landing: http://localhost:3000
- Chat: http://localhost:3000/chat
- Admin: http://localhost:3000/admin

### Full Stack (Docker — tanpa `npm run dev`)

```bash
# Dari folder root project
docker compose up --build

# Seed knowledge base (sekali, setelah stack jalan)
docker compose run --rm seed
```

| URL | Layanan |
|-----|---------|
| http://localhost:3000 | Chat UI (nginx) |
| http://localhost:3000/chat | Asisten |
| http://localhost:8080/docs | API Swagger |

> Qdrant image: gunakan `v1.12.5` (tag `v1.18.5` tidak ada di Docker Hub).

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Health + vector DB status |
| POST | `/api/v1/chat` | RAG query with citations |
| POST | `/api/v1/ingest` | Upload documents (PDF, DOCX, TXT) |
| GET | `/api/v1/admin/stats` | Platform metrics |
| GET | `/metrics` | Prometheus metrics |

## Configuration

See `backend/.env.example`. Key settings:

- `LLM_PROVIDER=mock|openai|google` — set API keys for production synthesis
- `QDRANT_URL` — vector database endpoint
- `REDIS_URL` — distributed cache

## Project Structure

```
KarenaAI/
├── app/                 # React frontend (Vite + Tailwind + shadcn)
├── backend/karena/      # FastAPI RAG platform
│   ├── rag/             # Hybrid retrieval, re-ranking, embeddings
│   ├── agents/          # Orchestrator (Google ADK integration point)
│   ├── ingestion/       # ETL, parsing, chunking
│   ├── memory/          # Conversation persistence
│   ├── cache/           # Multi-tier caching
│   └── prompts/         # Dynamic prompt engineering
├── infrastructure/      # Kubernetes, Terraform reference
├── docs/                # Architecture & product specification
└── docker-compose.yml
```

## Roadmap (PRD Phases)

| Phase | Weeks | Deliverables |
|-------|-------|--------------|
| 1 MVP | 1–4 | RAG pipeline, vector DB, ingestion, chat UI ✅ |
| 2 Enterprise | 5–8 | SSO, API gateway hardening, compliance policies |
| 3 SaaS | 9–12 | Multi-tenancy metering, DR, full observability |

## License

Proprietary — Ahmad Fashich Azzuhri Ramadhani
