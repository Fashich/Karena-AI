"""End-to-end RAG pipeline orchestration."""

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RAGResponse:
    answer: str
    sources: list[dict[str, Any]]
    confidence: float
    session_id: str
    latency_ms: float
    trace: dict = field(default_factory=dict)


class RAGPipeline:
    def __init__(
        self,
        retriever=None,
        reranker=None,
        llm=None,
        cache=None,
    ) -> None:
        self._compat_sync = any(dep is not None for dep in (retriever, reranker, llm, cache))
        self.retriever = retriever or self._load_retriever()
        self.reranker = reranker or self._load_reranker()
        self.llm = llm
        self.prompt_builder = self._load_prompt_builder()
        self.agent = self._load_agent()
        self.cache = cache or self._load_cache()
        self.memory = self._load_memory()

    def _load_retriever(self):
        from karena.rag.hybrid_retriever import get_hybrid_retriever

        return get_hybrid_retriever()

    def _load_reranker(self):
        from karena.rag.reranker import ReRanker

        return ReRanker()

    def _load_prompt_builder(self):
        from karena.prompts.builder import PromptBuilder

        return PromptBuilder()

    def _load_agent(self):
        from karena.agents.orchestrator import AgentOrchestrator

        return AgentOrchestrator()

    def _load_cache(self):
        from karena.cache.tiers import CacheTier

        return CacheTier()

    def _load_memory(self):
        from karena.memory.store import MemoryStore

        return MemoryStore()

    def _get_settings(self):
        from karena.config import get_settings

        return get_settings()

    def _get_tracer(self):
        from karena.observability.tracing import get_tracer

        return get_tracer()

    def _record_query(self, tenant_id: str, event_name: str, latency_ms: float, count: int) -> None:
        from karena.observability.metrics import record_query

        record_query(tenant_id, event_name, latency_ms, count)

    def _get_span_status(self):
        from karena.observability.tracing import SpanStatus

        return SpanStatus

    def query(
        self,
        question: str,
        *,
        session_id: str | None = None,
        tenant_id: str | None = None,
        user_id: str = "anonymous",
    ):
        if self._compat_sync:
            return self._query_sync_compat(question)
        return self._query_async(
            question,
            session_id=session_id,
            tenant_id=tenant_id,
            user_id=user_id,
        )

    def _query_sync_compat(self, question: str) -> dict[str, Any]:
        cache_get = getattr(self.cache, "get", None)
        if cache_get:
            cached = cache_get(question)
            if cached:
                return cached

        documents = self.retriever.retrieve(question)
        reranked = self.reranker.rerank(question, documents)
        if self.llm is not None:
            answer = self.llm.generate(question, reranked)
        else:
            answer = "Generated response"
        return {
            "answer": answer,
            "sources": reranked,
            "confidence": 0.9,
        }

    async def _query_async(
        self,
        question: str,
        *,
        session_id: str | None = None,
        tenant_id: str | None = None,
        user_id: str = "anonymous",
    ) -> RAGResponse:
        settings = self._get_settings()
        tenant_id = tenant_id or settings.default_tenant_id
        start = time.perf_counter()
        tracer = self._get_tracer()
        span_status = self._get_span_status()

        root_span = tracer.start_trace(
            "rag_query",
            {"tenant_id": tenant_id, "user_id": user_id, "question_length": len(question)},
        )

        cache_key = f"rag:{tenant_id}:{hash(question)}"
        cached = await self.cache.get_response(cache_key)
        if cached:
            latency_ms = (time.perf_counter() - start) * 1000
            self._record_query(tenant_id, "cache_hit", latency_ms, 0)
            tracer.add_event(root_span, "cache_hit", {"cache_key": cache_key})
            tracer.end_span(root_span, span_status.OK)
            trace = tracer.get_trace(root_span.trace_id)
            if trace:
                trace.end_time = time.time()
            return RAGResponse(**cached, latency_ms=latency_ms)

        try:
            session_id = session_id or await self.memory.create_session(user_id, tenant_id)
            history = await self.memory.get_recent_messages(session_id, limit=6)

            expanded_query = self._expand_query(question, history)
            retrieval_span = tracer.start_span(
                "hybrid_retrieval",
                {"tenant_id": tenant_id, "expanded_query_length": len(expanded_query)},
            )
            retrieved = await self.retriever.retrieve(expanded_query, tenant_id=tenant_id)
            tracer.end_span(retrieval_span, span_status.OK)

            rerank_span = tracer.start_span("semantic_reranking", {"input_count": len(retrieved)})
            reranked = self.reranker.rerank(expanded_query, retrieved)
            tracer.end_span(rerank_span, span_status.OK)

            prompt = self.prompt_builder.build(
                question=question,
                context_docs=reranked,
                history=history,
            )

            generation_span = tracer.start_span(
                "agent_generation",
                {"prompt_length": len(prompt), "llm_provider": settings.llm_provider},
            )
            answer, confidence = await self.agent.generate(prompt, question)
            tracer.end_span(generation_span, span_status.OK)

            sources = [
                {
                    "id": getattr(doc, "id", None) or (doc.get("id", "") if isinstance(doc, dict) else ""),
                    "title": getattr(doc, "source_title", None) or (doc.get("source_title", "") if isinstance(doc, dict) else ""),
                    "source_id": getattr(doc, "source_id", None) or (doc.get("source_id", "") if isinstance(doc, dict) else ""),
                    "excerpt": (
                        getattr(doc, "text", None)
                        or (doc.get("text", "") if isinstance(doc, dict) else "")
                    )[:300],
                    "score": round(getattr(doc, "score", 0.0), 4),
                    "channel": getattr(doc, "retrieval_channel", "") or (doc.get("retrieval_channel", "") if isinstance(doc, dict) else ""),
                }
                for doc in reranked[:10]
            ]

            await self.memory.add_message(session_id, "user", question)
            await self.memory.add_message(session_id, "assistant", answer, sources=sources)

            latency_ms = (time.perf_counter() - start) * 1000
            response = RAGResponse(
                answer=answer,
                sources=sources,
                confidence=confidence,
                session_id=session_id,
                latency_ms=latency_ms,
                trace={
                    "trace_id": root_span.trace_id,
                    "retrieved_count": len(retrieved),
                    "reranked_count": len(reranked),
                    "expanded_query": expanded_query,
                },
            )
            self._record_query(tenant_id, "success", latency_ms, len(retrieved))

            await self.cache.set_response(
                cache_key,
                {
                    "answer": answer,
                    "sources": sources,
                    "confidence": confidence,
                    "session_id": session_id,
                    "trace": response.trace,
                },
            )
            tracer.end_span(root_span, span_status.OK)
            trace = tracer.get_trace(root_span.trace_id)
            if trace:
                trace.end_time = time.time()
            return response
        except Exception as exc:
            latency_ms = (time.perf_counter() - start) * 1000
            self._record_query(tenant_id, "error", latency_ms, 0)
            tracer.record_error(root_span, exc)
            tracer.end_span(root_span, span_status.ERROR)
            trace = tracer.get_trace(root_span.trace_id)
            if trace:
                trace.end_time = time.time()
            raise

    def _expand_query(self, question: str, history: list[dict[str, Any]]) -> str:
        if not history:
            return question
        last_user = next(
            (m.get("content") for m in reversed(history) if m.get("role") == "user"),
            None,
        )
        if last_user and len(question.split()) < 6:
            return f"{last_user} {question}"
        return question

    def index_bm25_corpus(self, documents: list[dict[str, Any]]) -> None:
        self.retriever.index_corpus(documents)
