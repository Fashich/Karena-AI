"""
Web search service for KarenaAI Community Decision Intelligence Platform.

Providers (in priority order):
1. Tavily — LLM-optimized search, best quality
2. DuckDuckGo — fallback, no API key needed
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class WebSearchResult:
    title: str
    url: str
    content: str
    score: float = 0.0
    source: str = "web"

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "content": self.content[:500],
            "score": round(self.score, 3),
            "source": self.source,
        }


class WebSearchService:
    """
    Unified web search service with Tavily (primary) and
    DuckDuckGo (fallback) providers.
    """

    def __init__(self, tavily_api_key: str = "") -> None:
        self.tavily_api_key = tavily_api_key
        self._tavily_client: Optional[object] = None
        if tavily_api_key:
            try:
                from tavily import TavilyClient
                self._tavily_client = TavilyClient(api_key=tavily_api_key)
                logger.info("Tavily web search initialized")
            except Exception as e:
                logger.warning("Tavily init failed: %s", e)

    async def search(
        self,
        query: str,
        *,
        max_results: int = 5,
        search_depth: str = "basic",  # "basic" or "advanced"
        include_domains: list[str] | None = None,
    ) -> list[WebSearchResult]:
        """Search the web and return structured results."""
        if self._tavily_client:
            try:
                return await self._tavily_search(
                    query, max_results=max_results, search_depth=search_depth,
                    include_domains=include_domains,
                )
            except Exception as e:
                logger.warning("Tavily search failed, falling back to DuckDuckGo: %s", e)

        return await self._ddg_search(query, max_results=max_results)

    async def _tavily_search(
        self,
        query: str,
        max_results: int,
        search_depth: str,
        include_domains: list[str] | None,
    ) -> list[WebSearchResult]:
        import asyncio
        loop = asyncio.get_event_loop()

        kwargs: dict = {
            "query": query,
            "max_results": max_results,
            "search_depth": search_depth,
            "include_answer": False,
            "include_raw_content": False,
        }
        if include_domains:
            kwargs["include_domains"] = include_domains

        response = await loop.run_in_executor(
            None,
            lambda: self._tavily_client.search(**kwargs),  # type: ignore[union-attr]
        )

        results = []
        for r in response.get("results", []):
            results.append(WebSearchResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                content=r.get("content", ""),
                score=r.get("score", 0.5),
                source="tavily",
            ))
        return results

    async def _ddg_search(
        self,
        query: str,
        max_results: int,
    ) -> list[WebSearchResult]:
        import asyncio
        loop = asyncio.get_event_loop()

        def _sync_search():
            try:
                from duckduckgo_search import DDGS
                with DDGS() as ddgs:
                    return list(ddgs.text(query, max_results=max_results))
            except Exception as e:
                logger.warning("DuckDuckGo search failed: %s", e)
                return []

        raw = await loop.run_in_executor(None, _sync_search)
        return [
            WebSearchResult(
                title=r.get("title", ""),
                url=r.get("href", ""),
                content=r.get("body", ""),
                score=0.5,
                source="duckduckgo",
            )
            for r in raw
        ]

    def format_for_llm(self, results: list[WebSearchResult], query: str) -> str:
        """Format search results as context for LLM prompt."""
        if not results:
            return ""

        lines = [f"WEB SEARCH RESULTS for: {query}\n"]
        for i, r in enumerate(results, 1):
            lines.append(f"[{i}] {r.title}")
            lines.append(f"URL: {r.url}")
            lines.append(f"Content: {r.content[:400]}")
            lines.append("")

        return "\n".join(lines)


# ── Singleton ─────────────────────────────────────────────────
_instance: Optional[WebSearchService] = None


def get_web_search() -> WebSearchService:
    global _instance
    if _instance is None:
        from karena.config import get_settings
        settings = get_settings()
        api_key = getattr(settings, "tavily_api_key", "")
        _instance = WebSearchService(tavily_api_key=api_key)
    return _instance
