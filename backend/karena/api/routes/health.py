from fastapi import APIRouter

from karena.config import get_settings
from karena.rag.vector_store import get_vector_store

router = APIRouter()


@router.get("/health")
async def health():
    settings = get_settings()
    vector_status = "unknown"
    try:
        store = get_vector_store()
        info = await store.collection_info()
        vector_status = "healthy"
        points = info.get("points_count", 0)
    except Exception as e:
        vector_status = f"degraded: {e}"
        points = 0

    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "vector_store": settings.vector_store,
        "vector_db": vector_status,
        "indexed_chunks": points,
        "redis_required": False,
    }
