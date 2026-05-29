# Karena AI — System Architecture

## Design Principles

1. **Hybrid retrieval** — Dense vectors (Qdrant HNSW) + BM25 lexical fusion via RRF
2. **Two-stage re-ranking** — Cross-encoder scoring stub → LTR feature boost (extensible)
3. **Multi-tier cache** — L1 in-process, L2 Redis with tenant invalidation
4. **Hierarchical memory** — Short-term (session messages), durable SQLite/Postgres
5. **ADK-ready agents** — `AgentOrchestrator` delegates to OpenAI/Google; swap for Google ADK
6. **Defense in depth** — Encryption, audit logs, DLP hooks (Phase 2)

## RAG Pipeline Flow

```
User Query
    → Query expansion (session context)
    → Cache lookup (L1/L2)
    → Hybrid retrieval (dense + BM25, top-100)
    → Re-ranker (top-15)
    → Dynamic prompt build (context compression)
    → Agent / LLM synthesis
    → Citation packaging + memory persist
    → Response cache
```

## Component Map

| Module | Path | Responsibility |
|--------|------|----------------|
| Embeddings | `rag/embeddings.py` | Sentence-transformers, 384-dim vectors |
| Chunking | `rag/chunking.py` | Adaptive sentence-boundary chunks |
| Vector Store | `rag/vector_store.py` | Qdrant with tenant filters |
| Hybrid Retriever | `rag/hybrid_retriever.py` | Dense + BM25 RRF fusion |
| Re-ranker | `rag/reranker.py` | Two-stage relevance refinement |
| Pipeline | `rag/pipeline.py` | End-to-end orchestration |
| Agents | `agents/orchestrator.py` | Intent + LLM delegation |
| Prompts | `prompts/builder.py` | Versioned templates, few-shot |
| Cache | `cache/tiers.py` | Response + retrieval caching |
| Memory | `memory/store.py` | Session transcripts |
| Ingestion | `ingestion/etl.py` | Parse → chunk → embed → index |

## Scalability Targets

- **Uptime**: 99.9%
- **p95 latency**: < 1000ms end-to-end
- **Throughput**: Horizontal pod autoscaling on Kubernetes
- **Vector scale**: Qdrant sharding for billion-scale (production config)

## Integration Points (Phase 2+)

- Identity: Azure AD, Okta (OAuth2/OIDC)
- Ticketing: ServiceNow, Jira webhooks
- Messaging: Slack, Microsoft Teams embeds
- Productivity: Office 365, Google Workspace export

## Deployment Modes

- **Greenfield**: Terraform + K8s + GitOps (see `infrastructure/`)
- **Brownfield**: API gateway federation with legacy repos
- **Multi-tenant SaaS**: Namespace isolation + per-tenant Qdrant filters
