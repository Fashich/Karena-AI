"""In-process vector store for local dev when Docker/Qdrant is unavailable."""

from typing import Any

import numpy as np

from karena.config import get_settings
from karena.rag.chunking import DocumentChunk


class MemoryVectorStore:
    """Cosine-similarity search over in-memory vectors (dev / offline mode)."""

    def __init__(self) -> None:
        self._points: dict[str, dict[str, Any]] = {}
        settings = get_settings()
        self.collection = settings.qdrant_collection
        self.dimension = settings.embedding_dim

    async def ensure_collection(self) -> None:
        return None

    async def upsert_chunks(
        self,
        chunks: list[DocumentChunk],
        vectors: list[list[float]],
    ) -> int:
        for chunk, vector in zip(chunks, vectors):
            self._points[chunk.id] = {
                "vector": np.asarray(vector, dtype=np.float32),
                "text": chunk.text,
                "source_id": chunk.source_id,
                "source_title": chunk.source_title,
                "chunk_index": chunk.chunk_index,
                "tenant_id": chunk.tenant_id,
                **chunk.metadata,
            }
        return len(chunks)

    async def dense_search(
        self,
        query_vector: list[float],
        *,
        tenant_id: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        if not self._points:
            return []

        q = np.asarray(query_vector, dtype=np.float32)
        q_norm = np.linalg.norm(q) or 1.0

        scored: list[tuple[float, str]] = []
        for pid, payload in self._points.items():
            if payload.get("tenant_id") != tenant_id:
                continue
            v = payload["vector"]
            v_norm = np.linalg.norm(v) or 1.0
            score = float(np.dot(q, v) / (q_norm * v_norm))
            scored.append((score, pid))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, pid in scored[:limit]:
            p = self._points[pid]
            results.append(
                {
                    "id": pid,
                    "score": score,
                    "text": p.get("text", ""),
                    "source_id": p.get("source_id", ""),
                    "source_title": p.get("source_title", ""),
                    "metadata": p,
                }
            )
        return results

    async def delete_by_source(self, source_id: str, tenant_id: str) -> None:
        to_delete = [
            pid
            for pid, p in self._points.items()
            if p.get("source_id") == source_id and p.get("tenant_id") == tenant_id
        ]
        for pid in to_delete:
            del self._points[pid]

    async def collection_info(self) -> dict:
        return {
            "name": self.collection,
            "points_count": len(self._points),
            "status": "memory",
            "backend": "in-memory",
        }

    def all_documents(self, tenant_id: str) -> list[dict[str, Any]]:
        return [
            {
                "id": pid,
                "text": p.get("text", ""),
                "source_id": p.get("source_id", ""),
                "source_title": p.get("source_title", ""),
            }
            for pid, p in self._points.items()
            if p.get("tenant_id") == tenant_id
        ]
