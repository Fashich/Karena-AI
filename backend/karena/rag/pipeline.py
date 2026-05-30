"""End-to-end RAG pipeline orchestration."""

import time
from dataclasses import dataclass, field

from karena.agents.orchestrator import AgentOrchestrator
from karena.cache.tiers import CacheTier
from karena.config import get_settings
from karena.memory.store import MemoryStore
from karena.observability.metrics import record_query
from karena.observability.tracing import SpanStatus, get_tracer
from karena.prompts.builder import PromptBuilder
from karena.rag.hybrid_retriever import get_hybrid_retriever
from karena.rag.reranker import ReRanker


@dataclass
class RAGResponse:
    answer: str
    sources: list[dict]
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
        self.retriever = retriever or get_hybrid_retriever()
        self.reranker = reranker or ReRanker()
        self.llm = llm
        self.prompt_builder = PromptBuilder()
        self.agent = AgentOrchestrator()
        self.cache = cache or CacheTier()
        self.memory = MemoryStore()

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

    def _query_sync_compat(self, question: str) -> dict:
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
        settings = get_settings()
        tenant_id = tenant_id or settings.default_tenant_id
        start = time.perf_counter()
        tracer = get_tracer()
        root_span = tracer.start_trace(
            "rag_query",
            {"tenant_id": tenant_id, "user_id": user_id, "question_length": len(question)},
        )

        cache_key = f"rag:{tenant_id}:{hash(question)}"
        cached = await self.cache.get_response(cache_key)
        if cached:
            latency_ms = (time.perf_counter() - start) * 1000
            record_query(tenant_id, "cache_hit", latency_ms, 0)
            tracer.add_event(root_span, "cache_hit", {"cache_key": cache_key})
            tracer.end_span(root_span, SpanStatus.OK)
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
            tracer.end_span(retrieval_span, SpanStatus.OK)

            rerank_span = tracer.start_span("semantic_reranking", {"input_count": len(retrieved)})
            reranked = self.reranker.rerank(expanded_query, retrieved)
            tracer.end_span(rerank_span, SpanStatus.OK)

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
            tracer.end_span(generation_span, SpanStatus.OK)

            sources = [
                {
                    "id": doc.id,
                    "title": doc.source_title,
                    "source_id": doc.source_id,
                    "excerpt": doc.text[:300],
                    "score": round(doc.score, 4),
                    "channel": doc.retrieval_channel,
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
            record_query(tenant_id, "success", latency_ms, len(retrieved))

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
            tracer.end_span(root_span, SpanStatus.OK)
            trace = tracer.get_trace(root_span.trace_id)
            if trace:
                trace.end_time = time.time()
            return response
        except Exception as exc:
            latency_ms = (time.perf_counter() - start) * 1000
            record_query(tenant_id, "error", latency_ms, 0)
            tracer.record_error(root_span, exc)
            tracer.end_span(root_span, SpanStatus.ERROR)
            trace = tracer.get_trace(root_span.trace_id)
            if trace:
                trace.end_time = time.time()
            raise

    def _expand_query(self, question: str, history: list[dict]) -> str:
        if not history:
            return question
        last_user = next(
            (m["content"] for m in reversed(history) if m["role"] == "user"),
            None,
        )
        if last_user and len(question.split()) < 6:
            return f"{last_user} {question}"
        return question

    def index_bm25_corpus(self, documents: list[dict]) -> None:
        self.retriever.index_corpus(documents)
