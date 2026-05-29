"""Pydantic request/response models."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
  message: str = Field(..., min_length=1, max_length=8000)
  session_id: str | None = None
  tenant_id: str | None = None
  user_id: str = "anonymous"


class SourceCitation(BaseModel):
  id: str
  title: str
  source_id: str
  excerpt: str
  score: float
  channel: str


class ChatResponse(BaseModel):
  answer: str
  sources: list[SourceCitation]
  confidence: float
  session_id: str
  latency_ms: float


class FeedbackRequest(BaseModel):
  session_id: str
  rating: int = Field(..., ge=-1, le=1)
  comment: str | None = None


class IngestResponse(BaseModel):
  source_id: str
  chunks_indexed: int
  title: str
  message: str = "Document indexed successfully"
