# Karena AI
## Community Decision Intelligence Platform

> **APAC Generative AI Hackathon 2026 — Hack2Skill**
> Built by **Ahmad Fashich Azzuhri Ramadhani**

Karena AI is an enterprise-grade **AI-powered Decision Intelligence Platform** that unifies fragmented community and urban data into actionable insights — helping individuals, organisations, and city stakeholders make better decisions that improve everyday life and community well-being.

---

## Problem Statement Addressed

Modern APAC communities generate massive volumes of structured and unstructured data across urban mobility, healthcare, environment, citizen services, disaster response, education, and energy systems. **Transforming this information into actionable decisions remains a critical gap.** Karena AI closes this gap with:

- 🔍 **Natural language Q&A** over community knowledge bases (RAG)
- 🤖 **Multi-agent domain AI** — 7 specialist agents with deep community context
- 📊 **Predictive analytics** — time-series forecasting + anomaly detection
- 🖼️ **Multimodal AI** — image analysis for infrastructure damage, environmental conditions
- 🔔 **Real-time insights** — auto-generated, domain-specific recommendations
- 🔐 **Enterprise-grade** — PII detection, audit logs, DLP, OAuth2/OIDC, RBAC

---

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│  React Frontend · Landing | Dashboard | Chat | Admin           │
│  Decision Intelligence Dashboard (7 domains, live charts)     │
│  Multimodal Chat (text + image upload → Gemini Vision)        │
└─────────────────────────────┬──────────────────────────────────┘
                              │ REST /api/v1
┌─────────────────────────────▼──────────────────────────────────┐
│  FastAPI Gateway (Python 3.11+)                               │
│  ├── RAG Pipeline   : hybrid retrieval (dense + BM25) → rerank │
│  ├── Multi-Agent    : 7 domain specialist agents (ADK-ready)   │
│  ├── Analytics      : forecasting + anomaly detection          │
│  ├── Multimodal     : Gemini Vision / OpenAI GPT-4o            │
│  ├── Memory         : session transcripts + audit trail        │
│  └── Security       : PII/DLP, OIDC, API key lifecycle         │
└──────┬──────────────────┬──────────────────┬───────────────────┘
       │                  │                  │
   Qdrant             Redis             SQLite/Postgres
 (vectors)           (cache)            (memory/audit)
```

---

## Google Cloud Technology Stack

| Capability | Google Cloud / Technology |
|---|---|
| **LLM & RAG** | Gemini 2.0 Flash (`google-genai` SDK) |
| **Multimodal Vision** | Gemini Vision API (image → community insights) |
| **Agent Orchestration** | Google ADK-compatible multi-agent architecture |
| **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` (384-dim) |
| **Vector Search** | Qdrant HNSW (Vertex AI Matching Engine upgrade path) |
| **Deployment** | Cloud Run / Kubernetes (GKE) via Terraform |
| **Observability** | OpenTelemetry + Prometheus + Grafana |
| **CI/CD** | GitHub Actions |

---

## Community Domains (7 Specialist AI Agents)

| Domain | Agent | Key Metrics |
|---|---|---|
| 🚗 Urban Mobility | `UrbanMobilityAgent` | Congestion index, transit usage, commute time |
| 🏥 Healthcare | `HealthcareAgent` | Bed occupancy, ER wait, vaccination coverage |
| 🌿 Environment | `EnvironmentAgent` | AQI, carbon emissions, water quality |
| 👥 Citizen Services | `CitizenServicesAgent` | Request volume, resolution time, satisfaction |
| 🚨 Disaster Response | `DisasterResponseAgent` | Active incidents, early warnings, recovery rate |
| 📚 Education | `EducationAgent` | Enrolment, attendance, learning outcomes |
| ⚡ Energy & Utilities | `EnergyUtilitiesAgent` | Grid load, renewable share, outages |

---

## Key Innovation Features

### 1. Multi-Agent Domain Orchestration (ADK-Ready)
Queries are automatically classified into community domains and routed to specialist AI agents with deep domain context. Each agent provides not just answers, but **recommended actions, anomaly alerts, and predictive insights**.

### 2. Hybrid RAG Pipeline
- **Dense retrieval** via Qdrant HNSW vector search
- **Lexical retrieval** via BM25
- **Reciprocal Rank Fusion (RRF)** for result merging
- **Two-stage re-ranking** for relevance refinement
- **Source traceability** with confidence scores

### 3. Multimodal AI Analysis
Upload photos of infrastructure damage, environmental conditions, or incident scenes → **Gemini Vision** analyzes and returns severity assessment, structured findings, and recommended actions for city response teams.

### 4. Predictive Analytics Engine
- **Time-series forecasting** (linear trend + confidence intervals)
- **Anomaly detection** (z-score based with severity classification)
- **Auto-insight generation** per domain with impact classification
- Production upgrade path: Vertex AI AutoML, BigQuery ML

### 5. Enterprise Security & Compliance
- PII detection (GDPR, PDPA, CCPA, HIPAA)
- API key lifecycle (generate, rotate, revoke) with SHA256 hashing
- Session management with token revocation
- Comprehensive audit log for every interaction
- OAuth2/OIDC SSO (Azure AD, Google Workspace)

---

## Quick Start

### Option A — No Docker (Recommended)

```bash
cd backend
python -m venv .venv
# Windows:
.\.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env    # or: cp .env.example .env

mkdir data
python scripts/seed_knowledge.py
python run.py
# API: http://localhost:8080/docs
```

```bash
# Frontend (separate terminal)
cd app
npm install
npm run dev
# App: http://localhost:3000
```

### Option B — With Docker (Qdrant + Redis)

```bash
docker compose up --build
docker compose run --rm seed
```

| URL | Service |
|---|---|
| http://localhost:3000 | Landing Page |
| http://localhost:3000/dashboard | Decision Intelligence Dashboard |
| http://localhost:3000/chat | AI Assistant (text + image) |
| http://localhost:3000/admin | Admin Panel |
| http://localhost:8080/docs | API Swagger UI |
| http://localhost:8080/metrics | Prometheus Metrics |

---

## Configuration (`.env`)

```env
# LLM — Gemini (recommended for full multimodal support)
LLM_PROVIDER=google
GOOGLE_API_KEY=your-google-api-key
GOOGLE_MODEL=gemini-2.0-flash

# Or OpenAI
# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-...

# Vector store (production)
VECTOR_STORE=qdrant
QDRANT_URL=http://localhost:6333

# No-Docker mode (default)
VECTOR_STORE=memory
LLM_PROVIDER=mock
```

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Health + vector DB status |
| `POST` | `/api/v1/chat` | RAG query with citations |
| `POST` | `/api/v1/analytics/query` | Domain-routed multi-agent query |
| `GET` | `/api/v1/analytics/domains` | List 7 community domains |
| `GET` | `/api/v1/analytics/snapshot` | Real-time metrics snapshot |
| `POST` | `/api/v1/analytics/forecast` | Time-series forecasting |
| `POST` | `/api/v1/analytics/anomalies` | Anomaly detection |
| `GET` | `/api/v1/analytics/insights/{domain}` | AI-generated insights |
| `POST` | `/api/v1/analyze/image` | Gemini Vision multimodal analysis |
| `GET` | `/api/v1/analyze/status` | Multimodal capability status |
| `POST` | `/api/v1/ingest` | Upload documents (PDF, DOCX, TXT) |
| `GET` | `/api/v1/admin/stats` | Platform metrics |
| `GET` | `/metrics` | Prometheus metrics |

---

## Project Structure

```
KarenaAI/
├── app/                          # React 19 frontend (Vite + Tailwind + shadcn)
│   └── src/
│       ├── pages/
│       │   ├── Dashboard.tsx     # Decision Intelligence Dashboard (NEW)
│       │   ├── Chat.tsx          # Multimodal AI Chat (text + image)
│       │   ├── Landing.tsx       # Platform showcase
│       │   └── Admin.tsx         # System admin
│       └── sections/             # Landing page sections
├── backend/karena/               # FastAPI RAG platform (Python 3.11)
│   ├── domains/                  # Multi-domain AI agents (NEW)
│   │   └── agents.py             # 7 community specialist agents
│   ├── analytics/                # Predictive analytics engine (NEW)
│   │   └── engine.py             # Forecasting + anomaly + insights
│   ├── rag/                      # Hybrid retrieval pipeline
│   ├── agents/                   # Orchestrator (ADK-ready)
│   ├── api/routes/
│   │   ├── analytics.py          # Analytics API (NEW)
│   │   ├── multimodal.py         # Gemini Vision API (NEW)
│   │   └── chat.py               # RAG chat
│   ├── security/                 # PII, DLP, auth, audit
│   └── observability/            # OpenTelemetry, Prometheus
├── infrastructure/               # Kubernetes, Terraform, monitoring
└── docs/                         # Architecture & product specification
```

---

## Roadmap

| Phase | Status | Deliverables |
|---|---|---|
| 1 MVP | ✅ Done | RAG pipeline, vector DB, ingestion, chat UI |
| 2 Community AI | ✅ Done | 7 domain agents, analytics, multimodal, dashboard |
| 3 Enterprise | 🔄 Next | Full SSO, multi-tenancy metering, BigQuery connector |
| 4 Production | 📋 Planned | GKE auto-scaling, AlloyDB, Vertex AI integration |

---

## License

Proprietary — Ahmad Fashich Azzuhri Ramadhani · APAC Generative AI Hackathon 2026
