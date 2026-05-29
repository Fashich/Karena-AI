from fastapi import APIRouter

from karena.config import get_settings
from karena.rag.vector_store import get_vector_store

router = APIRouter()


@router.get("/admin/stats")
async def admin_stats():
    settings = get_settings()
    try:
        info = await get_vector_store().collection_info()
        vector_ok = True
    except Exception:
        info = {}
        vector_ok = False

    return {
        "tenant_id": settings.default_tenant_id,
        "environment": settings.environment,
        "vector_db": {
            "healthy": vector_ok,
            "collection": info.get("name", settings.qdrant_collection),
            "points_count": info.get("points_count", 0),
        },
        "embedding_model": settings.embedding_model,
        "llm_provider": settings.llm_provider,
        "sla_targets": {
            "uptime": "99.9%",
            "p95_latency_ms": 1000,
        },
    }
