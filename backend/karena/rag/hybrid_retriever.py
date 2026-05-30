"""Hybrid dense + BM25 retrieval with learned fusion."""

from dataclasses import dataclass
from typing import Any

from rank_bm25 import BM25Okapi

from karena.rag.embeddings import get_embedding_service
from karena.rag.vector_store import get_vector_store


@dataclass
class RetrievedDocument:
    id: str
    text: str
    source_id: str
    source_title: str
    score: float
    retrieval_channel: str


_retriever_instance: "HybridRetriever | None" = None


def get_hybrid_retriever() -> "HybridRetriever":
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = HybridRetriever()
    return _retriever_instance


def refresh_bm25_corpus(tenant_id: str) -> None:
    """Rebuild BM25 index from current vector store (after ingestion)."""
    from karena.rag.vector_store import get_vector_store

    store = get_vector_store()
    if not hasattr(store, "all_documents"):
        return
    docs = store.all_documents(tenant_id)  # type: ignore[attr-defined]
    get_hybrid_retriever().index_corpus(docs)


class HybridRetriever:
    """Combines Qdrant dense search with in-memory BM25 over corpus cache."""

    def __init__(
        self,
        dense_retriever=None,
        bm25_retriever=None,
        alpha: float | None = None,
    ) -> None:
        self.dense_retriever = dense_retriever
        self.bm25_retriever = bm25_retriever
        self.alpha = 0.7 if alpha is None else alpha
        self._bm25_index: BM25Okapi | None = None
        self._bm25_docs: list[dict[str, Any]] = []

    def index_corpus(self, documents: list[dict[str, Any]]) -> None:
        self._bm25_docs = documents
        tokenized = [doc["text"].lower().split() for doc in documents]
        self._bm25_index = BM25Okapi(tokenized) if tokenized else None

    def retrieve(
        self,
        query: str,
        *,
        tenant_id: str | None = None,
        top_k: int | None = None,
    ):
        if self.dense_retriever is not None or self.bm25_retriever is not None:
            return self._retrieve_sync_compat(query, top_k=top_k)
        return self._retrieve_async(query, tenant_id=tenant_id or "default", top_k=top_k)

    def _retrieve_sync_compat(self, query: str, top_k: int | None = None) -> list[dict[str, Any]]:
        k = top_k or 10
        dense_results = (
            self.dense_retriever.retrieve(query, top_k=k) if self.dense_retriever else []
        )
        sparse_results = self.bm25_retriever.retrieve(query, top_k=k) if self.bm25_retriever else []
        scores: dict[str, dict[str, Any]] = {}
        for doc in dense_results:
            doc_id = doc.get("id", doc.get("content", ""))
            scores[doc_id] = {**doc, "score": float(doc.get("score", 0.0)) * self.alpha}
        for doc in sparse_results:
            doc_id = doc.get("id", doc.get("content", ""))
            weighted = float(doc.get("score", 0.0)) * (1.0 - self.alpha)
            if doc_id in scores:
                scores[doc_id]["score"] += weighted
            else:
                scores[doc_id] = {**doc, "score": weighted}
        return sorted(scores.values(), key=lambda item: item.get("score", 0.0), reverse=True)[:k]

    async def _retrieve_async(
        self,
        query: str,
        *,
        tenant_id: str,
        top_k: int | None = None,
    ) -> list[RetrievedDocument]:
        from karena.config import get_settings

        settings = get_settings()
        k = top_k or settings.retrieval_top_k
        dense_k = min(k, 50)

        embeddings = get_embedding_service()
        vector_store = get_vector_store()
        query_vector = embeddings.embed_query(query)

        dense_results = await vector_store.dense_search(
            query_vector, tenant_id=tenant_id, limit=dense_k
        )

        sparse_results: list[dict[str, Any]] = []
        if self._bm25_index and self._bm25_docs:
            tokens = query.lower().split()
            scores = self._bm25_index.get_scores(tokens)
            ranked = sorted(zip(self._bm25_docs, scores), key=lambda x: x[1], reverse=True)[
                :dense_k
            ]
            sparse_results = [
                {**doc, "score": float(score), "channel": "bm25"}
                for doc, score in ranked
                if score > 0
            ]

        fused = self._fuse_results(dense_results, sparse_results, settings.hybrid_dense_weight)
        return fused[:k]

    def _fuse_results(
        self,
        dense: list[dict],
        sparse: list[dict],
        dense_weight: float,
    ) -> list[RetrievedDocument]:
        scores: dict[str, dict] = {}

        for rank, doc in enumerate(dense):
            doc_id = doc["id"]
            rrf = 1.0 / (60 + rank + 1)
            scores[doc_id] = {
                "doc": doc,
                "score": rrf * dense_weight,
                "channels": ["dense"],
            }

        sparse_weight = 1.0 - dense_weight
        for rank, doc in enumerate(sparse):
            doc_id = doc.get("id", doc.get("source_id", "") + str(rank))
            rrf = 1.0 / (60 + rank + 1)
            if doc_id in scores:
                scores[doc_id]["score"] += rrf * sparse_weight
                scores[doc_id]["channels"].append("bm25")
            else:
                scores[doc_id] = {
                    "doc": doc,
                    "score": rrf * sparse_weight,
                    "channels": ["bm25"],
                }

        sorted_docs = sorted(scores.values(), key=lambda x: x["score"], reverse=True)
        results: list[RetrievedDocument] = []
        for item in sorted_docs:
            doc = item["doc"]
            results.append(
                RetrievedDocument(
                    id=doc.get("id", ""),
                    text=doc.get("text", ""),
                    source_id=doc.get("source_id", ""),
                    source_title=doc.get("source_title", "Unknown"),
                    score=item["score"],
                    retrieval_channel="+".join(item["channels"]),
                )
            )
        return results
