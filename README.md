<div align="center">

<img src="app/public/icons/images/KarenaAI-Logo.png" alt="Karena AI Logo" width="120" style="border-radius: 16px; margin-bottom: 16px;" />

# KARENA AI
### Community Decision Intelligence Platform

**APAC Generative AI Hackathon 2026 · Hack2Skill**

[![Team](https://img.shields.io/badge/Team-SovereignSwarm-blue?style=flat-square)](https://hack2skill.com)
[![Builder](https://img.shields.io/badge/Builder-Ahmad%20Fashich%20Azzuhri%20Ramadhani-blue?style=flat-square)](https://github.com)
[![Stack](https://img.shields.io/badge/Stack-FastAPI%20%7C%20React%2019%20%7C%20Qdrant%20%7C%20Groq-darkblue?style=flat-square)](https://github.com)
[![LLM](https://img.shields.io/badge/LLM-Groq%20LLaMA%203.3%2070B-orange?style=flat-square)](https://groq.com)
[![Search](https://img.shields.io/badge/Web%20Search-Tavily%20%2B%20DuckDuckGo-green?style=flat-square)](https://tavily.com)

</div>

---

## 🎯 Problem Statement

Modern APAC communities generate massive volumes of structured and unstructured data from urban systems, healthcare networks, environmental sensors, public services, and citizen feedback. **Transforming this fragmented data into actionable decisions remains a critical challenge** for city stakeholders.

**Karena AI** solves this by unifying community data across **7 specialist domains** into a single, AI-powered decision intelligence platform — enabling individuals, communities, organisations, and city stakeholders to analyse information, generate insights, predict outcomes, and make better decisions that improve everyday life.

---

## ✨ Key Features

### 🤖 Multi-Agent Domain Intelligence
7 specialist AI agents, each with deep APAC community context:

| Domain | Agent | Key Intelligence |
|---|---|---|
| 🚗 Urban Mobility | `UrbanMobilityAgent` | Traffic congestion, transit ridership, ATSC, EV adoption |
| 🏥 Healthcare | `HealthcareAgent` | Bed occupancy, disease surveillance, vaccination coverage |
| 🌿 Environment | `EnvironmentAgent` | AQI, carbon emissions, water quality, climate resilience |
| 👥 Citizen Services | `CitizenServicesAgent` | Service requests, digital adoption, citizen satisfaction |
| 🚨 Disaster Response | `DisasterResponseAgent` | Early warning, resource deployment, community resilience |
| 📚 Education | `EducationAgent` | Enrollment, attendance, learning outcomes, EdTech |
| ⚡ Energy & Utilities | `EnergyUtilitiesAgent` | Grid load, renewable share, NRW, smart utilities |

### 🔍 Hybrid RAG Pipeline
- **Dense retrieval** via Qdrant HNSW vector search (384-dim embeddings)
- **BM25 lexical retrieval** for keyword precision
- **Reciprocal Rank Fusion (RRF)** for optimal result merging
- **Two-stage re-ranking** for relevance refinement
- **Source traceability** with confidence scores per citation

### 🌐 Real-Time Web Search
- **Tavily** (primary) — LLM-optimised search, real-time results
- **DuckDuckGo** (fallback) — no API key required
- Toggle in chat UI — augments RAG with live web context
- Searches news, Wikipedia, research papers, government sites

### 📊 Decision Intelligence Dashboard
- 7 domain tabs with live KPI cards
- Real-time metrics from backend API (30-second polling)
- AreaChart + BarChart visualisations (recharts)
- AI-generated insights per domain
- Live alert feed
- Connected / Offline status indicator

### 🖼️ Multimodal AI Analysis
- Upload images of infrastructure damage, environmental conditions, or incidents
- Gemini Vision / GPT-4o Vision analysis
- Returns severity assessment + recommended city response actions
- Supports JPEG, PNG, WebP

### 📄 Document Intelligence
- Upload PDF (text + OCR for scanned documents), DOCX, TXT
- Real-time ingestion progress (page-by-page OCR with Tesseract)
- Async background processing with polling endpoint
- Adaptive chunking (512 tokens, 64-token overlap)

### 🔐 Enterprise Security
- PII detection compliant with **GDPR, PDPA Singapore, CCPA, HIPAA**
- DLP (Data Loss Prevention) for all document uploads and chat queries
- API key lifecycle management with SHA-256 hashing
- Full audit logging of every user interaction
- OAuth2/OIDC SSO ready (Azure AD, Google Workspace)
- Role-Based Access Control (RBAC) — 6 roles

### 📈 Predictive Analytics
- Time-series forecasting with confidence intervals
- Anomaly detection (z-score, severity classification)
- Auto-insight generation per community domain
- Upgrade path: Vertex AI AutoML, BigQuery ML

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  React 19 Frontend                                               │
│  Landing | Dashboard (7 domains) | Chat | Admin                 │
│  Recharts · shadcn/ui · Tailwind CSS · TypeScript               │
└────────────────────────┬────────────────────────────────────────┘
                         │ REST /api/v1  (Vite proxy)
┌────────────────────────▼────────────────────────────────────────┐
│  FastAPI Backend (Python 3.11+)                                 │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐ │
│  │  RAG Pipeline│  │  Multi-Agent │  │  Analytics Engine     │ │
│  │  Hybrid      │  │  7 Domains   │  │  Forecast + Anomaly   │ │
│  │  Dense+BM25  │  │  ADK-ready   │  │  Auto-insights        │ │
│  └──────────────┘  └──────────────┘  └───────────────────────┘ │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐ │
│  │  Web Search  │  │  Multimodal  │  │  Security Layer       │ │
│  │  Tavily+DDG  │  │  Gemini      │  │  PII·DLP·Audit·RBAC   │ │
│  └──────────────┘  └──────────────┘  └───────────────────────┘ │
└───────┬─────────────────────┬───────────────────┬──────────────┘
        │                     │                   │
   Qdrant Cloud          SQLite/Postgres      Redis Cache
  (Vector Store)         (Memory+Audit)      (optional)
```

---

## 🔄 System Flow Diagram

```mermaid
flowchart TD
    subgraph USER["👤 USER LAYER"]
        U1[City Stakeholder / Planner]
        U2[Community Manager]
        U3[Emergency Responder]
        U4[Platform Administrator]
    end

    subgraph FRONTEND["🖥️ FRONTEND — React 19 + TypeScript"]
        F2[Decision Dashboard\n7 Domain Tabs + Live KPIs]
        F3[AI Chat Interface\nNatural Language Query]
        F4[Admin Panel\nDocument Ingestion + Stats]
        F5[Image Upload\nMultimodal Analysis]
    end

    subgraph GATEWAY["🔐 API GATEWAY — FastAPI"]
        G1[Authentication\nOAuth2 / JWT / OIDC]
        G2[Rate Limiting\nToken Bucket]
        G3[PII Scanner\nGDPR / PDPA / HIPAA]
        G4[DLP Layer\nData Loss Prevention]
        G5[Audit Logger\nImmutable Logs]
        G6[RBAC Enforcer\n6 Permission Roles]
    end

    subgraph ORCHESTRATOR["🧠 AGENT ORCHESTRATOR"]
        O1[Intent Classifier]
        O2[Domain Router]
        O3[Query Expander\nSynonym + Context]
        O4[Session Memory\nConversation Context]
    end

    subgraph AGENTS["🤖 DOMAIN SPECIALIST AGENTS"]
        A1[🚗 Urban Mobility Agent\nTraffic · Transit · EV]
        A2[🏥 Healthcare Agent\nBed Occupancy · Disease · Vaccine]
        A3[🌿 Environment Agent\nAQI · Carbon · Water]
        A4[👥 Citizen Services Agent\nRequests · Satisfaction · Digital]
        A5[🚨 Disaster Response Agent\nEarly Warning · Resources · Recovery]
        A6[📚 Education Agent\nEnrolment · Attendance · Outcomes]
        A7[⚡ Energy & Utilities Agent\nGrid · Renewable · Smart Utility]
    end

    subgraph RAG["🔍 HYBRID RAG PIPELINE"]
        R1[Dense Retrieval\nQdrant HNSW 384-dim]
        R2[BM25 Lexical Retrieval\nKeyword Precision]
        R3[Reciprocal Rank Fusion\nResult Merging]
        R4[Cross-Encoder Re-Ranker\nStage 1 — Top 100 → Top 20]
        R5[Learned-to-Rank\nStage 2 — Personalized]
        R6[Context Packager\nSource Attribution + Citations]
    end

    subgraph SEARCH["🌐 WEB SEARCH"]
        S1[Tavily API\nLLM-Optimised Search]
        S2[DuckDuckGo Fallback\nNo Key Required]
    end

    subgraph LLM["💬 LLM & VISION LAYER"]
        L1[Gemini 2.0 Flash\nText + Reasoning]
        L2[Gemini Vision\nImage Analysis]
        L3[Groq LLaMA 3.3 70B\nOpenAI-Compatible]
        L4[Dynamic Prompt Engine\nTemplate + Few-Shot]
    end

    subgraph ANALYTICS["📊 ANALYTICS ENGINE"]
        AN1[Time-Series Forecasting\nConfidence Intervals]
        AN2[Anomaly Detection\nZ-Score + Severity]
        AN3[Auto-Insight Generator\nPer-Domain Summaries]
        AN4[Live Metrics Snapshot\n30s Polling]
    end

    subgraph INGESTION["📄 DOCUMENT INGESTION"]
        I1[Document Parser\nPDF · DOCX · TXT]
        I2[OCR Engine\nTesseract Page-by-Page]
        I3[Adaptive Chunker\n512 tokens / 64 overlap]
        I4[Embedding Generator\nall-MiniLM-L6-v2]
        I5[Async Job Tracker\nProgress Polling]
    end

    subgraph STORAGE["🗄️ STORAGE LAYER"]
        ST1[(Qdrant Cloud\nVector Store)]
        ST2[(SQLite / Postgres\nMemory + Audit)]
        ST3[(Redis Cache\nMulti-Tier)]
    end

    subgraph INFRA["☁️ INFRASTRUCTURE"]
        IN1[Cloud Run / GKE\nTerraform Provisioned]
        IN2[OpenTelemetry\nDistributed Tracing]
        IN3[Prometheus + Grafana\nMetrics + Alerting]
        IN4[GitHub Actions\nCI/CD Pipeline]
    end

    U1 & U2 & U3 --> F2 & F3 & F5
    U4 --> F4

    F2 & F3 & F4 & F5 --> G1
    G1 --> G2 --> G3 --> G4 --> G5 --> G6

    G6 --> O1 --> O2 --> O3
    O2 --> O4

    O2 --> A1 & A2 & A3 & A4 & A5 & A6 & A7

    A1 & A2 & A3 & A4 & A5 & A6 & A7 --> R1 & R2
    R1 & R2 --> R3 --> R4 --> R5 --> R6

    R1 <--> ST1
    R5 --> ST3

    O3 --> S1 --> L4
    S1 -- fallback --> S2 --> L4

    R6 --> L4
    L4 --> L1 & L3
    F5 --> L2

    L1 --> AN3
    AN1 & AN2 & AN4 --> F2

    F4 --> I1 --> I2 --> I3 --> I4 --> ST1
    I5 <--> F4

    G5 --> ST2
    O4 <--> ST2

    IN1 -.-> FRONTEND & GATEWAY & AGENTS & RAG
    IN2 -.-> GATEWAY & AGENTS & RAG
    IN3 -.-> IN2
    IN4 -.-> IN1
```

---

## 🎭 Use Case Diagram

```mermaid
graph LR
    subgraph ACTORS["ACTORS"]
        CK[👤 City Stakeholder]
        CM[👥 Community Manager]
        ER[🚨 Emergency Responder]
        ADM[🔧 Platform Admin]
        SYS[⚙️ System / Scheduler]
    end

    subgraph UC_CHAT["CONVERSATIONAL AI"]
        UC1([Query Domain in Natural Language])
        UC2([Receive AI-Generated Insight])
        UC3([Toggle Real-Time Web Search])
        UC4([View Source Citations])
        UC5([Follow-Up Multi-Turn Conversation])
    end

    subgraph UC_DASH["DECISION DASHBOARD"]
        UC6([View Live Domain KPIs])
        UC7([Explore Domain Analytics Tab])
        UC8([View Active Alert Feed])
        UC9([Monitor Platform Uptime Status])
    end

    subgraph UC_ANALYTICS["PREDICTIVE ANALYTICS"]
        UC10([Request Time-Series Forecast])
        UC11([Detect Anomalies in Domain Data])
        UC12([View Auto-Generated Domain Insights])
        UC13([Set Confidence Interval Parameters])
    end

    subgraph UC_MULTIMODAL["MULTIMODAL ANALYSIS"]
        UC14([Upload Infrastructure Image])
        UC15([Receive Severity Assessment])
        UC16([Get Recommended Response Actions])
        UC17([Analyze Environmental Condition Photo])
    end

    subgraph UC_INGEST["DOCUMENT INTELLIGENCE"]
        UC18([Upload PDF / DOCX / TXT Document])
        UC19([Monitor OCR Ingestion Progress])
        UC20([Query Ingested Document via RAG])
        UC21([Manage Knowledge Base])
    end

    subgraph UC_SECURITY["SECURITY & COMPLIANCE"]
        UC22([Authenticate via OAuth2 / SSO])
        UC23([Manage API Key Lifecycle])
        UC24([View Audit Logs])
        UC25([Configure RBAC Roles])
        UC26([Trigger PII / DLP Scan])
    end

    subgraph UC_SYSTEM["SYSTEM OPERATIONS"]
        UC27([Auto-Poll Backend Metrics Every 30s])
        UC28([Run Anomaly Detection Scheduler])
        UC29([Refresh Vector Index Incrementally])
        UC30([Execute CI/CD Deployment Pipeline])
        UC31([Export Prometheus Metrics])
    end

    CK --> UC1 & UC2 & UC3 & UC4 & UC5
    CK --> UC6 & UC7 & UC8 & UC9
    CK --> UC10 & UC12
    CK --> UC22

    CM --> UC1 & UC5
    CM --> UC6 & UC7 & UC8
    CM --> UC10 & UC11 & UC12
    CM --> UC14 & UC15 & UC16 & UC17
    CM --> UC22

    ER --> UC1 & UC2 & UC4
    ER --> UC8 & UC9
    ER --> UC11
    ER --> UC14 & UC15 & UC16
    ER --> UC22

    ADM --> UC18 & UC19 & UC20 & UC21
    ADM --> UC22 & UC23 & UC24 & UC25 & UC26
    ADM --> UC9

    SYS --> UC27 & UC28 & UC29 & UC30 & UC31
```

---

## 🖼️ UI Mock Diagram

```
╔═════════════════════════════════════════════════════════════════════════════════════════════════════╗
║  🔷 KARENA AI  [Beta]                    Platform    Intelligence    Security    [Dashboard] [Try AI→] ║
╠═════════════════════════════════════════════════════════════════════════════════════════════════════╣
║                                                                                                     ║
║  ┌──────────────────────────── PAGE: LANDING ─────────────────────────────────────────────────┐   ║
║  │                                                                                              │   ║
║  │  ╔══ APAC Generative AI Hackathon 2026 · Hack2Skill ══╗    ╔══ LIVE PLATFORM METRICS ══╗   │   ║
║  │  ║                                                     ║    ║  ┌──────────┬──────────┐  ║   │   ║
║  │  ║  Community                                          ║    ║  │  1,247   │    3     │  ║   │   ║
║  │  ║  Decision Intelligence                              ║    ║  │ AI Dec.  │  Alerts  │  ║   │   ║
║  │  ║  Platform                                           ║    ║  ├──────────┼──────────┤  ║   │   ║
║  │  ║                                                     ║    ║  │   28     │  99.9%   │  ║   │   ║
║  │  ║  AI-powered insights across 7 community domains     ║    ║  │  Comm.   │  Uptime  │  ║   │   ║
║  │  ║  Powered by RAG + Gemini for APAC stakeholders      ║    ║  └──────────┴──────────┘  ║   │   ║
║  │  ║                                                     ║    ║  Urban   ████████░░  72   ║   │   ║
║  │  ║  [📊 Open Dashboard]   [🧠 Try AI Assistant]        ║    ║  Health  █████████░  78   ║   │   ║
║  │  ║                                                     ║    ║  Environ ██████░░░░  52   ║   │   ║
║  │  ║  7          98%        99.9%       Gemini           ║    ║  ● Backend · 12s ago       ║   │   ║
║  │  ║  AI Domains RAG Acc.   Uptime      Vision+Lang      ║    ╚═══════════════════════════╝   │   ║
║  │  ╚═════════════════════════════════════════════════════╝                                    │   ║
║  │                                                                                              │   ║
║  │  ── Built on ──  [Gemini 2.0 Flash] [Google ADK] [Cloud Run] [RAG+Qdrant] [Vertex AI]      │   ║
║  │                                                                                              │   ║
║  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────┐  │   ║
║  │  │ 🚗 Urban   │ │ 🏥 Health  │ │ 🌿 Environ │ │ 👥 Citizen │ │ 🚨 Disaster│ │ 📚 Edu   │  │   ║
║  │  │ Mobility   │ │ care       │ │ ment       │ │ Services   │ │ Response   │ │ cation   │  │   ║
║  │  │            │ │            │ │            │ │            │ │            │ │          │  │   ║
║  │  │ Traffic ·  │ │ Bed Occ. · │ │ AQI ·      │ │ Requests · │ │ Warnings · │ │ Enroll · │  │   ║
║  │  │ Transit ·  │ │ Disease ·  │ │ Carbon ·   │ │ Satisf. ·  │ │ Resources· │ │ Attend · │  │   ║
║  │  │ EV Adopt   │ │ Vaccine    │ │ Water      │ │ Digital    │ │ Recovery   │ │ Outcomes │  │   ║
║  │  │ View ins → │ │ View ins → │ │ View ins → │ │ View ins → │ │ View ins → │ │ View  → │  │   ║
║  │  └────────────┘ └────────────┘ └────────────┘ └────────────┘ └────────────┘ └──────────┘  │   ║
║  └──────────────────────────────────────────────────────────────────────────────────────────┘   ║
║                                                                                                     ║
║  ┌──────────────────────────── PAGE: DECISION DASHBOARD ─────────────────────────────────────┐   ║
║  │                                                                                              │   ║
║  │  [🚗 Urban] [🏥 Health] [🌿 Env] [👥 Citizen] [🚨 Disaster] [📚 Edu] [⚡ Energy]           │   ║
║  │  ─────────────────────────────────────────────────────────────────────────────────────      │   ║
║  │                                                                                              │   ║
║  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │   ║
║  │  │ CONGESTION   │  │   TRANSIT    │  │  EV ADOPT.   │  │   ALERTS     │                   │   ║
║  │  │    72%       │  │  1.2M/day    │  │    18%       │  │      3       │                   │   ║
║  │  │  ▲ +4% ↑     │  │  ▼ -2% ↓    │  │  ▲ +1.2% ↑   │  │  ⚠ Active    │                   │   ║
║  │  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘                   │   ║
║  │                                                                                              │   ║
║  │  Traffic Trend (7 days)                         Peak Hours Heatmap                          │   ║
║  │  ┌─────────────────────────────────────────┐   ┌──────────────────────────────────────┐    │   ║
║  │  │ 100 │                    ╭──╮            │   │       06  09  12  15  18  21         │    │   ║
║  │  │  80 │           ╭──╮  ╭──╯  ╰──╮        │   │  Mon  ░░░▓▓▓███▓▓▓▓▓▓░░░░░░░        │    │   ║
║  │  │  60 │      ╭────╯  ╰──╯        ╰────╮   │   │  Tue  ░░░▓▓▓███▓▓▓▓▓▓░░░░░░░        │    │   ║
║  │  │  40 │  ╭───╯                        │   │   │  Wed  ░░░▓▓▓███████▓▓░░░░░░░        │    │   ║
║  │  │     └──────────────────────────────  │   │   │  Thu  ░░░▓▓▓▓▓▓▓▓▓▓▓░░░░░░░        │    │   ║
║  │  │      Mon  Tue  Wed  Thu  Fri  Sat    │   │   │  Fri  ░░░███████████░░░░░░░         │    │   ║
║  │  └─────────────────────────────────────┘   └──────────────────────────────────────┘    │   ║
║  │                                                                                              │   ║
║  │  🧠 AI-Generated Insights                       🚨 Live Alert Feed                          │   ║
║  │  ┌─────────────────────────────────────────┐   ┌──────────────────────────────────────┐    │   ║
║  │  │ "Peak congestion detected on northern   │   │ 🔴 HIGH  Road closure Jl. Sudirman   │    │   ║
║  │  │  corridor during 07:00–09:00 window.    │   │          Sector B-7 — 14:32          │    │   ║
║  │  │  EV adoption trending +1.2% in eastern  │   │ 🟡 MED   Transit delay Line 3        │    │   ║
║  │  │  districts. Recommend transit frequency │   │          Delayed 12min — 14:15       │    │   ║
║  │  │  increase on Route 47 and Route 12."    │   │ 🔵 INFO  AQI spike Zone D forecasted │    │   ║
║  │  │                  [Refresh Insights]      │   │          for 16:00–18:00 — 13:58     │    │   ║
║  │  └─────────────────────────────────────────┘   └──────────────────────────────────────┘    │   ║
║  └──────────────────────────────────────────────────────────────────────────────────────────┘   ║
║                                                                                                     ║
║  ┌──────────────────────────── PAGE: AI CHAT ASSISTANT ──────────────────────────────────────┐   ║
║  │                                                                                              │   ║
║  │  ┌──────────────────────────────────────────────────────────────────────────────────────┐  │   ║
║  │  │  🧠 Community AI Assistant                              🌐 Web Search [ON ●]  [Clear] │  │   ║
║  │  └──────────────────────────────────────────────────────────────────────────────────────┘  │   ║
║  │                                                                                              │   ║
║  │  ┌── CONVERSATION THREAD ───────────────────────────────────────────────────────────────┐  │   ║
║  │  │                                                                                        │  │   ║
║  │  │           ┌──────────────────────────────────────────────────────────────────────┐    │  │   ║
║  │  │  👤 User  │ What is the current air quality situation in Jakarta?                 │    │  │   ║
║  │  │           └──────────────────────────────────────────────────────────────────────┘    │  │   ║
║  │  │                                                                                        │  │   ║
║  │  │  ┌──────────────────────────────────────────────────────────────────────────────────┐ │  │   ║
║  │  │  │ 🤖 KarenaAI  [🌿 EnvironmentAgent]                                               │ │  │   ║
║  │  │  │                                                                                   │ │  │   ║
║  │  │  │  Jakarta's current AQI reads 142 — Unhealthy for Sensitive Groups.               │ │  │   ║
║  │  │  │  PM2.5 at 58 μg/m³, driven by vehicular and industrial emissions.               │ │  │   ║
║  │  │  │                                                                                   │ │  │   ║
║  │  │  │  📍 Sources:                                                                     │ │  │   ║
║  │  │  │  [1] BMKG Air Quality Report Jul 2026 ·············· 0.94                        │ │  │   ║
║  │  │  │  [2] EnvironmentAgent KnowledgeBase ················ 0.91                        │ │  │   ║
║  │  │  │  [3] Tavily Web Search — Jakarta AQI Live ·········· 0.88                        │ │  │   ║
║  │  │  │  [👍] [👎] [📋 Copy]                                                              │ │  │   ║
║  │  │  └──────────────────────────────────────────────────────────────────────────────────┘ │  │   ║
║  │  │                                                                                        │  │   ║
║  │  │  ┌──────────────────────────────────────────────────────────────────────────────────┐ │  │   ║
║  │  │  │ 🤖 KarenaAI  [🚨 DisasterResponseAgent + Gemini Vision]  [📎 flood_damage.jpg]   │ │  │   ║
║  │  │  │                                                                                   │ │  │   ║
║  │  │  │  Severity: 🔴 HIGH  │  Category: Flood Infrastructure Damage                     │ │  │   ║
║  │  │  │  Inundation: ~3.2 km²  │  Water Level: +1.4–1.8m  │  At Risk: ~12,400           │ │  │   ║
║  │  │  │  Bridge Integrity: ⚠ Compromised                                                 │ │  │   ║
║  │  │  │                                                                                   │ │  │   ║
║  │  │  │  → Deploy emergency response units to sector B-7 immediately                     │ │  │   ║
║  │  │  │  → Activate early warning system for downstream zones C-3, C-4                  │ │  │   ║
║  │  │  │  → Coordinate BNPB resource deployment within 2-hour window                     │ │  │   ║
║  │  │  └──────────────────────────────────────────────────────────────────────────────────┘ │  │   ║
║  │  └──────────────────────────────────────────────────────────────────────────────────────┘  │   ║
║  │                                                                                              │   ║
║  │  [📎 Upload Image/Doc]  ┌────────────────────────────────────────┐  ┌──────────────────┐  │   ║
║  │                         │  Ask about any community domain...      │  │     Send  →      │  │   ║
║  │                         └────────────────────────────────────────┘  └──────────────────┘  │   ║
║  └──────────────────────────────────────────────────────────────────────────────────────────┘   ║
║                                                                                                     ║
║  ┌──────────────────────────── PAGE: ADMIN PANEL ────────────────────────────────────────────┐   ║
║  │                                                                                              │   ║
║  │  ┌────────────────┬──────────────────────────────────────────────────────────────────────┐ │   ║
║  │  │ 📊 Statistics  │  Platform Overview                                                    │ │   ║
║  │  │ 📄 Ingest Docs │  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐             │ │   ║
║  │  │ 🔑 API Keys    │  │    2,847       │  │     156        │  │    99.9%      │             │ │   ║
║  │  │ 👥 Users/RBAC  │  │  Documents     │  │   API Keys     │  │   Uptime      │             │ │   ║
║  │  │ 📋 Audit Log   │  └───────────────┘  └───────────────┘  └───────────────┘             │ │   ║
║  │  │ ⚙️  Settings   │                                                                        │ │   ║
║  │  │                │  Document Ingestion                                                    │ │   ║
║  │  │  Ahmad F.A.R.  │  ┌─────────────────────────────────────────────────────────────────┐ │ │   ║
║  │  │  [Admin Role]  │  │   📄  Drag & drop PDF, DOCX, or TXT files here                  │ │ │   ║
║  │  │                │  │               or  [Browse Files]                                 │ │ │   ║
║  │  │                │  └─────────────────────────────────────────────────────────────────┘ │ │   ║
║  │  │                │                                                                        │ │   ║
║  │  │                │  ● Ingesting  Jakarta_Health_Report_2026.pdf                          │ │   ║
║  │  │                │  ┌─────────────────────────────────────────────────────────────────┐ │ │   ║
║  │  │                │  │  ████████████████████░░░░░░  Page 18 of 24  —  78%              │ │ │   ║
║  │  │                │  │  OCR · Tesseract · Adaptive Chunking (512 tokens / 64 overlap)  │ │ │   ║
║  │  │                │  └─────────────────────────────────────────────────────────────────┘ │ │   ║
║  │  │                │                                                                        │ │   ║
║  │  │                │  ✅ Completed  APAC_Urban_Policy_2025.pdf   324 chunks · 2m 14s ago   │ │   ║
║  │  │                │  ✅ Completed  HealthInfra_Singapore.docx   189 chunks · 5m 08s ago   │ │   ║
║  │  └────────────────┴──────────────────────────────────────────────────────────────────────┘ │   ║
║  └──────────────────────────────────────────────────────────────────────────────────────────┘   ║
║                                                                                                     ║
╠═════════════════════════════════════════════════════════════════════════════════════════════════════╣
║  🔷 KARENA AI  ·  Community Decision Intelligence  ·  APAC Generative AI Hackathon 2026           ║
║  Built with Gemini · RAG · Google ADK · FastAPI · React 19 · Qdrant                               ║
╚═════════════════════════════════════════════════════════════════════════════════════════════════════╝
```

---

## 🛠️ Google Cloud & Technology Stack

| Category | Technology |
|---|---|
| **LLM** | Groq LLaMA 3.3 70B (OpenAI-compatible) / Gemini 2.0 Flash |
| **Vision AI** | Gemini Vision / GPT-4o multimodal |
| **Agent Framework** | Google ADK-compatible multi-agent architecture |
| **Vector Search** | Qdrant Cloud HNSW (upgrade: Vertex AI Matching Engine) |
| **Embeddings** | sentence-transformers/all-MiniLM-L6-v2 (384-dim) |
| **Web Search** | Tavily API + DuckDuckGo fallback |
| **Deployment** | Cloud Run / GKE via Terraform |
| **Observability** | OpenTelemetry + Prometheus + Grafana |
| **CI/CD** | GitHub Actions |

---

## 🚀 Quick Start

### Option A — No Docker (Recommended for local dev)

```bash
# Backend
cd backend
python -m venv .venv

# Windows
.\.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env     # Windows
# cp .env.example .env     # macOS/Linux

# Edit .env — set LLM_PROVIDER, API keys
mkdir data
python run.py
# API: http://localhost:8080/docs
```

```bash
# Frontend (new terminal)
cd app
npm install
npm run dev
# App: http://localhost:3000
```

### Option B — Docker Compose

```bash
docker compose up --build
```

---

## ⚙️ Environment Configuration

```env
# LLM Provider
LLM_PROVIDER=openai
OPENAI_API_KEY=gsk_...                          # Groq API key (free)
OPENAI_BASE_URL=https://api.groq.com/openai/v1
OPENAI_MODEL=llama-3.3-70b-versatile

# Or: Google Gemini
# LLM_PROVIDER=google
# GOOGLE_API_KEY=your-google-api-key
# GOOGLE_MODEL=gemini-2.0-flash

# Vector Store
VECTOR_STORE=qdrant                             # or "memory" for dev
QDRANT_URL=https://your-cluster.qdrant.io:6333
QDRANT_API_KEY=your-qdrant-api-key

# Web Search
TAVILY_API_KEY=tvly-...                         # Free: 1,000 searches/month

# Auth
REQUIRE_AUTH=false
JWT_SECRET=change-in-production
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | System health + vector DB status |
| `POST` | `/api/v1/chat` | RAG query + optional web search |
| `GET` | `/api/v1/analytics/domains` | List 7 community domains |
| `GET` | `/api/v1/analytics/snapshot` | Live metrics snapshot (all domains) |
| `GET` | `/api/v1/analytics/insights/{domain}` | AI-generated domain insights |
| `POST` | `/api/v1/analytics/forecast` | Time-series forecasting |
| `POST` | `/api/v1/analytics/anomalies` | Anomaly detection |
| `POST` | `/api/v1/analytics/query` | Domain-routed multi-agent query |
| `POST` | `/api/v1/analyze/image` | Gemini Vision multimodal analysis |
| `GET` | `/api/v1/analyze/status` | Vision capability status |
| `POST` | `/api/v1/search/web` | Direct web search endpoint |
| `POST` | `/api/v1/ingest` | Document upload (PDF/DOCX/TXT) |
| `GET` | `/api/v1/ingest/progress/{job_id}` | Real-time ingestion progress |
| `GET` | `/api/v1/stats` | Platform admin statistics |
| `GET` | `/metrics` | Prometheus metrics |

---

## 📁 Project Structure

```
KarenaAI/
├── app/                           # React 19 frontend
│   └── src/
│       ├── pages/
│       │   ├── Landing.tsx        # Professional landing page
│       │   ├── Dashboard.tsx      # 7-domain decision intelligence dashboard
│       │   ├── Chat.tsx           # AI chat with web search + image upload
│       │   └── Admin.tsx          # Platform admin + document ingestion
│       ├── lib/
│       │   └── api.ts             # Type-safe API client
│       └── sections/              # Landing page sections
├── backend/
│   └── karena/
│       ├── agents/
│       │   └── orchestrator.py    # LLM orchestration (Groq/Gemini/Mock)
│       ├── analytics/
│       │   └── engine.py          # Forecasting + anomaly + insights
│       ├── api/routes/
│       │   ├── chat.py            # RAG chat + web search
│       │   ├── analytics.py       # Domain analytics API
│       │   ├── multimodal.py      # Gemini Vision API
│       │   ├── ingest.py          # Async document ingestion
│       │   └── search.py          # Web search API
│       ├── domains/
│       │   └── agents.py          # 7 specialist domain agents
│       ├── ingestion/
│       │   ├── parser.py          # PDF/DOCX parser + async OCR
│       │   └── jobs.py            # Ingestion job tracking
│       ├── rag/                   # Hybrid RAG pipeline
│       ├── search/
│       │   └── web_search.py      # Tavily + DuckDuckGo web search
│       └── security/              # PII, DLP, audit, RBAC
├── infrastructure/                # Kubernetes + Terraform + monitoring
└── docs/                          # Architecture + product specification
```

---

## 🗺️ Roadmap

| Phase | Status | Deliverables |
|---|---|---|
| 1 — Core RAG | ✅ Done | Hybrid retrieval, vector DB, chat UI |
| 2 — Community AI | ✅ Done | 7 domain agents, analytics, multimodal, web search |
| 3 — Production | 🔄 Next | GKE deployment, BigQuery connector, full SSO |
| 4 — Scale | 📋 Planned | Vertex AI, AlloyDB, federated multi-city deployment |

---

## 👤 About

**Team:** SovereignSwarm  
**Builder:** Ahmad Fashich Azzuhri Ramadhani  
**NIM:** 23051214209  
**Institution:** Universitas Negeri Surabaya (UNESA) — S1 Sistem Informasi  
**Event:** APAC Generative AI Hackathon 2026 · Hack2Skill  

---

<div align="center">

Built with ❤️ for APAC communities · Powered by RAG + Groq + Qdrant + Tavily

</div>
