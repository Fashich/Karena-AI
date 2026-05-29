"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from karena.api.routes import admin, chat, escalation, health, ingest
from karena.config import get_settings
from karena.memory.store import init_db
from karena.observability.metrics import setup_metrics
from karena.rag.embeddings import get_embedding_service
from karena.rag.vector_store import get_vector_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    await init_db()
    vector_store = get_vector_store()
    await vector_store.ensure_collection()
    get_embedding_service()  # warm model load
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
            },
            "frontend": "http://localhost:3000/chat",
        }

    app.include_router(health.router, prefix=prefix, tags=["health"])
    app.include_router(chat.router, prefix=prefix, tags=["chat"])
    app.include_router(escalation.router, prefix=prefix, tags=["escalation"])
    app.include_router(ingest.router, prefix=prefix, tags=["ingest"])
    app.include_router(admin.router, prefix=prefix, tags=["admin"])

    setup_metrics(app)
    return app


app = create_app()
