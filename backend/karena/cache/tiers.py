"""Multi-tier distributed caching with graceful Redis fallback."""

import json
from typing import Any

from karena.config import get_settings

_redis_client = None
_memory_cache: dict[str, Any] = {}


def _get_redis():
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        import redis.asyncio as redis

        settings = get_settings()
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        return _redis_client
    except Exception:
        return None


class CacheTier:
    """L1: in-process memory. L2: Redis for query-response and retrieval caches."""

    async def get_response(self, key: str) -> dict | None:
        if key in _memory_cache:
            return _memory_cache[key]

        client = _get_redis()
        if client:
            try:
                raw = await client.get(f"karena:response:{key}")
                if raw:
                    return json.loads(raw)
            except Exception:
                pass
        return None

    async def set_response(self, key: str, value: dict) -> None:
        _memory_cache[key] = value
        if len(_memory_cache) > 500:
            oldest = next(iter(_memory_cache))
            del _memory_cache[oldest]

        client = _get_redis()
        if client:
            try:
                settings = get_settings()
                await client.setex(
                    f"karena:response:{key}",
                    settings.cache_ttl_seconds,
                    json.dumps(value),
                )
            except Exception:
                pass

    async def invalidate_tenant(self, tenant_id: str) -> None:
        keys_to_delete = [k for k in _memory_cache if tenant_id in k]
        for k in keys_to_delete:
            del _memory_cache[k]

        client = _get_redis()
        if client:
            try:
                async for key in client.scan_iter(f"karena:response:*{tenant_id}*"):
                    await client.delete(key)
            except Exception:
                pass
