"""Adaptive document chunking with metadata enrichment."""

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class DocumentChunk:
  id: str
  text: str
  source_id: str
  source_title: str
  chunk_index: int
  tenant_id: str
  metadata: dict = field(default_factory=dict)


def chunk_text(
  text: str,
  *,
  source_id: str,
  source_title: str,
  tenant_id: str,
  chunk_size: int = 512,
  chunk_overlap: int = 64,
  extra_metadata: dict | None = None,
) -> list[DocumentChunk]:
  """Split text into overlapping chunks respecting sentence boundaries."""
  text = re.sub(r"\s+", " ", text).strip()
  if not text:
    return []

  sentences = re.split(r"(?<=[.!?])\s+", text)
  chunks: list[DocumentChunk] = []
  current: list[str] = []
  current_len = 0
  index = 0

  def flush() -> None:
    nonlocal index, current, current_len
    if not current:
      return
    chunk_text_val = " ".join(current)
    meta = {
      "created_at": datetime.now(timezone.utc).isoformat(),
      **(extra_metadata or {}),
    }
    chunks.append(
      DocumentChunk(
        id=str(uuid.uuid4()),
        text=chunk_text_val,
        source_id=source_id,
        source_title=source_title,
        chunk_index=index,
        tenant_id=tenant_id,
        metadata=meta,
      )
    )
    index += 1
    overlap_sentences: list[str] = []
    overlap_len = 0
    for s in reversed(current):
      if overlap_len + len(s) > chunk_overlap:
        break
      overlap_sentences.insert(0, s)
      overlap_len += len(s)
    current = overlap_sentences
    current_len = overlap_len

  for sentence in sentences:
    if current_len + len(sentence) > chunk_size and current:
      flush()
    current.append(sentence)
    current_len += len(sentence)

  flush()
  return chunks
