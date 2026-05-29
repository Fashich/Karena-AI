"""Seed pilot knowledge base for demos."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from karena.config import get_settings
from karena.ingestion.etl import ingest_document
from karena.memory.store import init_db
from karena.rag.hybrid_retriever import refresh_bm25_corpus
from karena.rag.vector_store import get_vector_store

SAMPLE_DOCS = [
  {
    "filename": "apac-data-governance.md",
    "title": "APAC Data Governance Policy",
    "content": """
# APAC Data Governance Policy

## Data Retention
Customer records for APAC financial services clients must be retained for 7 years
following account closure. Inactive accounts transition to encrypted archival after
24 months of inactivity.

## Cross-Border Transfers
Data residency requirements mandate primary storage within the originating APAC jurisdiction.
Cross-border transfers require documented legal basis and Data Protection Impact Assessment.

## Audit Requirements
All access to compliance-critical data objects must be logged with immutable audit trails.
Subject access requests must be fulfilled within 30 calendar days per GDPR-aligned standards.
""",
  },
  {
    "filename": "karena-architecture.md",
    "title": "Karena AI Reference Architecture",
    "content": """
# Karena AI Reference Architecture

## RAG Pipeline
The platform implements hybrid retrieval combining dense vector search (Qdrant HNSW)
with BM25 lexical matching. A two-stage re-ranker refines top-100 candidates to top-15
passages for LLM context injection.

## Deployment
Greenfield deployments use Terraform IaC, Kubernetes orchestration, and GitOps CI/CD.
Brownfield integrations connect via API gateway with federated SSO (Azure AD, Okta).

## SLA Targets
99.9% uptime, sub-1 second p95 response latency, multi-region failover with
automated health checks and Prometheus/Grafana observability stack.
""",
  },
  {
    "filename": "support-escalation.md",
    "title": "Support Escalation Playbook",
    "content": """
# Support Escalation Playbook

## Tier 1 Resolution
Knowledge workers should query Karena AI before escalating. Target MTTR reduction: 30%.

## Escalation Criteria
Escalate to human experts when: confidence score below 0.5, compliance-sensitive queries
without source citations, or user explicitly requests human agent via /escalate command.

## Integration
ServiceNow and Jira webhooks receive full query context including retrieval trace and
session transcript for seamless handoff.
""",
  },
]


async def main():
  await init_db()
  store = get_vector_store()
  await store.ensure_collection()

  for doc in SAMPLE_DOCS:
    result = await ingest_document(
      filename=doc["filename"],
      content=doc["content"].encode("utf-8"),
      title=doc["title"],
    )
    print(f"Indexed {result.title}: {result.chunks_indexed} chunks")

  settings = get_settings()
  refresh_bm25_corpus(settings.default_tenant_id)

  info = await store.collection_info()
  print(f"Collection ready: {info['points_count']} total points ({info.get('backend', 'qdrant')})")


if __name__ == "__main__":
  asyncio.run(main())
