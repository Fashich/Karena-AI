"""
Web Search API route.

POST /api/v1/search/web  — search the web and return results
GET  /api/v1/search/status — check web search availability
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from karena.search.web_search import get_web_search

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["web-search"])


class WebSearchRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Search query")
    max_results: int = Field(5, ge=1, le=10)
    search_depth: str = Field("basic", description="basic or advanced")
    domains: list[str] | None = Field(None, description="Restrict to these domains")


@router.get("/status")
async def search_status():
    """Check web search availability."""
    svc = get_web_search()
    has_tavily = svc._tavily_client is not None
    return {
        "available": True,
        "provider": "tavily" if has_tavily else "duckduckgo",
        "tavily_configured": has_tavily,
        "fallback": "duckduckgo",
    }


@router.post("/web")
async def web_search(req: WebSearchRequest):
    """Search the web and return structured results."""
    try:
        svc = get_web_search()
        results = await svc.search(
            req.query,
            max_results=req.max_results,
            search_depth=req.search_depth,
            include_domains=req.domains,
        )
        return {
            "query": req.query,
            "results": [r.to_dict() for r in results],
            "count": len(results),
            "provider": results[0].source if results else "none",
        }
    except Exception as e:
        logger.exception("Web search error")
        raise HTTPException(status_code=500, detail=str(e))
