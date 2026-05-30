"""Two-stage re-ranking: cross-encoder style scoring + feature-based LTR stub."""

from karena.config import get_settings
from karena.rag.hybrid_retriever import RetrievedDocument


class ReRanker:
    """Stage-1: semantic overlap scoring. Stage-2: authority/freshness features."""

    def rerank(
        self,
        query: str,
        documents: list[RetrievedDocument],
        *,
        top_k: int | None = None,
    ) -> list[RetrievedDocument]:
        settings = get_settings()
        k = top_k or settings.rerank_top_k
        query_tokens = set(query.lower().split())

        scored: list[tuple[float, RetrievedDocument]] = []
        for doc in documents:
            doc_tokens = set(doc.text.lower().split())
            overlap = len(query_tokens & doc_tokens) / max(len(query_tokens), 1)
            cross_score = overlap * 0.6 + doc.score * 0.4
            authority_boost = 0.05 if doc.source_title else 0.0
            final = cross_score + authority_boost
            scored.append((final, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        reranked = []
        for score, doc in scored[:k]:
            reranked.append(
                RetrievedDocument(
                    id=doc.id,
                    text=doc.text,
                    source_id=doc.source_id,
                    source_title=doc.source_title,
                    score=score,
                    retrieval_channel=doc.retrieval_channel + "+rerank",
                )
            )
        return reranked


class SemanticReranker:
    """Cross-encoder compatibility reranker for legacy unit tests."""

    def __init__(self, model_name: str) -> None:
        from sentence_transformers import CrossEncoder

        self.model_name = model_name
        self._model = CrossEncoder(model_name)

    def rerank(self, query: str, documents: list[dict], top_k: int = 5) -> list[dict]:
        pairs = [(query, doc.get("content", doc.get("text", ""))) for doc in documents]
        scores = self._model.predict(pairs)
        ranked = []
        for doc, score in zip(documents, scores):
            ranked.append({**doc, "score": float(score)})
        ranked.sort(key=lambda doc: doc["score"], reverse=True)
        return ranked[:top_k]
