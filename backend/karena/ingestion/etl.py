"""ETL pipeline: parse â†’ chunk â†’ embed â†’ index."""

import uuid
from dataclasses import dataclass

from karena.config import get_settings
from karena.rag.chunking import chunk_text
from karena.rag.embeddings import get_embedding_service
from karena.rag.vector_store import get_vector_store


@dataclass
class IngestionResult:
    source_id: str
    chunks_indexed: int
    title: str


class ETLPipeline:
    """Compatibility wrapper for older document-ingestion callers."""

    async def process(
        self,
        *,
        filename: str,
        content: bytes,
        title: str | None = None,
        tenant_id: str | None = None,
    ) -> dict:
        result = await ingest_document(
            filename=filename,
            content=content,
            title=title,
            tenant_id=tenant_id,
        )
        return {
            "document_id": result.source_id,
            "status": "indexed",
            "chunks_indexed": result.chunks_indexed,
            "title": result.title,
        }


async def ingest_document(
    *,
    filename: str,
    content: bytes,
    title: str | None = None,
    tenant_id: str | None = None,
) -> IngestionResult:
    from karena.ingestion.parser import parse_file

    settings = get_settings()
    tenant_id = tenant_id or settings.default_tenant_id
    source_id = str(uuid.uuid4())
    doc_title = title or filename

    text = parse_file(filename, content)
    chunks = chunk_text(
        text,
        source_id=source_id,
        source_title=doc_title,
        tenant_id=tenant_id,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        extra_metadata={"filename": filename},
    )

    if not chunks:
        return IngestionResult(source_id=source_id, chunks_indexed=0, title=doc_title)

    embeddings = get_embedding_service()
    raw = embeddings.embed_texts([c.text for c in chunks]); vectors = raw.tolist() if hasattr(raw, "tolist") else raw

    vector_store = get_vector_store()
    count = await vector_store.upsert_chunks(chunks, vectors)

    from karena.rag.hybrid_retriever import refresh_bm25_corpus
    from karena.rag.drift import get_drift_detector

    refresh_bm25_corpus(tenant_id)
    get_drift_detector().update_baseline(tenant_id, [c.text for c in chunks])

    return IngestionResult(
        source_id=source_id,
        chunks_indexed=count,
        title=doc_title,
    )
