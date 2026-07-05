
async def _auto_seed():
    try:
        from karena.ingestion.etl import ingest_document
        docs = [
            ("Karena AI Reference Architecture", "architecture-doc",
             "Karena AI is a Community Decision Intelligence Platform built on hybrid RAG (dense HNSW + BM25), FastAPI backend, React 19 frontend, and 7 specialist domain agents (Urban Mobility, Healthcare, Environment, Citizen Services, Disaster Response, Education, Energy). Uses Groq LLaMA, multi-tenant RBAC, PII detection, OpenTelemetry observability."),
            ("APAC Data Governance Policy", "data-governance",
             "APAC data retention policy requires minimum 7 years per PDPA Singapore, GDPR. PII encrypted at rest and in transit. Data localization in Indonesia GR 71/2019, Malaysia PDPA 2010, Thailand PDPA 2019. Cross-border transfers need explicit consent and DPA."),
            ("Community Decision Intelligence Domains", "domain-guide",
             "7 domains: Urban Mobility traffic and transit, Healthcare capacity and vaccination, Environment AQI and carbon, Citizen Services requests and resolution, Disaster Response early warning and recovery, Education enrollment and outcomes, Energy and Utilities grid and renewables. Each has specialist AI agents."),
            ("Support Escalation Playbook", "escalation-playbook",
             "Tier 1 general queries via AI assistant. Escalate Tier 2 when confidence below 60 percent or compliance issues. Tier 3 for security incidents. SLA: Tier 1 equals 2 hours, Tier 2 equals 4 hours, Tier 3 equals 1 hour."),
        ]
        for title, source, content_text in docs:
            await ingest_document(
                filename=source + ".txt",
                content=content_text.encode("utf-8"),
                title=title,
                tenant_id="default",
            )
        import logging
        logging.getLogger(__name__).info("Auto-seed complete: %d documents", len(docs))
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("Auto-seed failed: %s", e)
"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from karena.api.routes import admin, auth, chat, compliance, escalation, health, ingest, tracing
from karena.api.routes import analytics as analytics_router
from karena.api.routes import multimodal as multimodal_router
from karena.api.gateway import get_gateway
from karena.config import get_settings
from karena.memory.store import init_db
from karena.observability.metrics import setup_metrics
from karena.rag.embeddings import get_embedding_service
from karena.rag.vector_store import get_vector_store
from karena.security.audit import AuditEventType, get_audit_logger
from karena.security.oidc import initialize_oidc_providers


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()  # Initialize settings
    await init_db()
    vector_store = get_vector_store()
    await vector_store.ensure_collection()
    await _auto_seed()
    get_embedding_service()  # warm model load

    if settings.oauth2_provider and settings.oauth2_client_id:
        await initialize_oidc_providers()

        if settings.oauth2_issuer:
            get_gateway().configure_oauth2(
                provider=settings.oauth2_provider,
                client_id=settings.oauth2_client_id,
                client_secret=settings.oauth2_client_secret or "",
                issuer=settings.oauth2_issuer,
            )

    get_audit_logger(settings.audit_db_path).log(
        AuditEventType.SYSTEM_STARTUP,
        actor_id="system",
        actor_type="service",
        action="startup",
        resource_type="api",
        tenant_id=settings.default_tenant_id,
        details={
            "environment": settings.environment,
            "vector_store": settings.vector_store,
            "oidc_enabled": bool(settings.oauth2_provider and settings.oauth2_issuer),
        },
    )
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Enterprise RAG Knowledge Intelligence Platform",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    prefix = settings.api_prefix

    @app.get("/", include_in_schema=False)
    async def root():
        return {
            "service": settings.app_name,
            "version": settings.app_version,
            "status": "running",
            "message": "API is up. Use the links below — there is no page at /.",
            "links": {
                "docs": "/docs",
                "health": f"{prefix}/health",
                "chat": f"{prefix}/chat",
                "escalate": f"{prefix}/escalate",
                "admin": f"{prefix}/admin/stats",
                "traces": f"{prefix}/traces",
                "metrics": "/metrics",
            },
            "frontend": "http://localhost:3000/chat",
        }

    app.include_router(health.router, prefix=prefix, tags=["health"])
    app.include_router(chat.router, prefix=prefix, tags=["chat"])
    app.include_router(escalation.router, prefix=prefix, tags=["escalation"])
    app.include_router(ingest.router, prefix=prefix, tags=["ingest"])
    app.include_router(admin.router, prefix=prefix, tags=["admin"])
    app.include_router(auth.router, prefix=prefix, tags=["auth"])
    app.include_router(compliance.router, prefix=prefix, tags=["compliance"])
    app.include_router(tracing.router, prefix=prefix, tags=["observability"])
    # Community Decision Intelligence (hackathon extensions)
    app.include_router(analytics_router.router, prefix=prefix, tags=["analytics"])
    app.include_router(multimodal_router.router, prefix=prefix, tags=["multimodal"])

    setup_metrics(app)
    return app


app = create_app()
