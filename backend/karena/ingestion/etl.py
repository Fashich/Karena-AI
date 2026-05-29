"""ETL pipeline: parse → chunk → embed → index."""

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
  vectors = embeddings.embed_texts([c.text for c in chunks]).tolist()

  vector_store = get_vector_store()
  count = await vector_store.upsert_chunks(chunks, vectors)

  from karena.rag.hybrid_retriever import refresh_bm25_corpus

  refresh_bm25_corpus(tenant_id)

  return IngestionResult(
    source_id=source_id,
    chunks_indexed=count,
    title=doc_title,
  )
