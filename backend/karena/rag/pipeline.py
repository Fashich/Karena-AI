"""End-to-end RAG pipeline orchestration."""

import time
from dataclasses import dataclass, field

from karena.agents.orchestrator import AgentOrchestrator
from karena.cache.tiers import CacheTier
from karena.config import get_settings
from karena.memory.store import MemoryStore
from karena.prompts.builder import PromptBuilder
from karena.rag.hybrid_retriever import RetrievedDocument, get_hybrid_retriever
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
  def __init__(self) -> None:
    self.retriever = get_hybrid_retriever()
    self.reranker = ReRanker()
    self.prompt_builder = PromptBuilder()
    self.agent = AgentOrchestrator()
    self.cache = CacheTier()
    self.memory = MemoryStore()

  async def query(
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

    cache_key = f"rag:{tenant_id}:{hash(question)}"
    cached = await self.cache.get_response(cache_key)
    if cached:
      return RAGResponse(**cached, latency_ms=(time.perf_counter() - start) * 1000)

    session_id = session_id or await self.memory.create_session(user_id, tenant_id)
    history = await self.memory.get_recent_messages(session_id, limit=6)

    expanded_query = self._expand_query(question, history)
    retrieved = await self.retriever.retrieve(
      expanded_query, tenant_id=tenant_id
    )
    reranked = self.reranker.rerank(expanded_query, retrieved)

    prompt = self.prompt_builder.build(
      question=question,
      context_docs=reranked,
      history=history,
    )

    answer, confidence = await self.agent.generate(prompt, question)

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
        "retrieved_count": len(retrieved),
        "reranked_count": len(reranked),
        "expanded_query": expanded_query,
      },
    )

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
    return response

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
