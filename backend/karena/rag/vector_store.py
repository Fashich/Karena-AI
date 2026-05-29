"""Vector database — Qdrant (production) or in-memory (local dev without Docker)."""

from functools import lru_cache
from typing import Any, Protocol

from karena.config import get_settings
from karena.rag.chunking import DocumentChunk


class VectorStoreProtocol(Protocol):
    async def ensure_collection(self) -> None: ...
    async def upsert_chunks(
        self, chunks: list[DocumentChunk], vectors: list[list[float]]
    ) -> int: ...
    async def dense_search(
        self, query_vector: list[float], *, tenant_id: str, limit: int = 50
    ) -> list[dict[str, Any]]: ...
    async def delete_by_source(self, source_id: str, tenant_id: str) -> None: ...
    async def collection_info(self) -> dict: ...


class QdrantVectorStore:
    def __init__(self) -> None:
        from qdrant_client import AsyncQdrantClient
        from qdrant_client.http import models as qmodels

        self._qmodels = qmodels
        settings = get_settings()
        # Don't pass `check_compatibility` to avoid passing unexpected kwargs
        # down into httpx for older client/server combinations.
        self.client = AsyncQdrantClient(url=settings.qdrant_url)
        self.collection = settings.qdrant_collection
        self.dimension = settings.embedding_dim

    async def ensure_collection(self) -> None:
        collections = await self.client.get_collections()
        names = {c.name for c in collections.collections}
        if self.collection not in names:
            await self.client.create_collection(
                collection_name=self.collection,
                vectors_config=self._qmodels.VectorParams(
                    size=self.dimension,
                    distance=self._qmodels.Distance.COSINE,
                ),
            )

    async def upsert_chunks(
        self,
        chunks: list[DocumentChunk],
        vectors: list[list[float]],
    ) -> int:
        points = [
            self._qmodels.PointStruct(
                id=chunk.id,
                vector=vector,
                payload={
                    "text": chunk.text,
                    "source_id": chunk.source_id,
                    "source_title": chunk.source_title,
                    "chunk_index": chunk.chunk_index,
                    "tenant_id": chunk.tenant_id,
                    **chunk.metadata,
                },
            )
            for chunk, vector in zip(chunks, vectors)
        ]
        await self.client.upsert(collection_name=self.collection, points=points)
        return len(points)

    async def dense_search(
        self,
        query_vector: list[float],
        *,
        tenant_id: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        results = await self.client.search(
            collection_name=self.collection,
            query_vector=query_vector,
            limit=limit,
            query_filter=self._qmodels.Filter(
                must=[
                    self._qmodels.FieldCondition(
                        key="tenant_id",
                        match=self._qmodels.MatchValue(value=tenant_id),
                    )
                ]
            ),
        )
        return [
            {
                "id": str(hit.id),
                "score": hit.score,
                "text": hit.payload.get("text", ""),
                "source_id": hit.payload.get("source_id", ""),
                "source_title": hit.payload.get("source_title", ""),
                "metadata": hit.payload,
            }
            for hit in results
        ]

    async def delete_by_source(self, source_id: str, tenant_id: str) -> None:
        await self.client.delete(
            collection_name=self.collection,
            points_selector=self._qmodels.FilterSelector(
                filter=self._qmodels.Filter(
                    must=[
                        self._qmodels.FieldCondition(
                            key="source_id",
                            match=self._qmodels.MatchValue(value=source_id),
                        ),
                        self._qmodels.FieldCondition(
                            key="tenant_id",
                            match=self._qmodels.MatchValue(value=tenant_id),
                        ),
                    ]
                )
            ),
        )

    async def collection_info(self) -> dict:
        info = await self.client.get_collection(self.collection)
        return {
            "name": self.collection,
            "points_count": info.points_count,
            "status": str(info.status),
            "backend": "qdrant",
        }


@lru_cache
def get_vector_store() -> VectorStoreProtocol:
    settings = get_settings()
    if settings.vector_store == "qdrant":
        return QdrantVectorStore()
    from karena.rag.memory_store import MemoryVectorStore

    return MemoryVectorStore()
