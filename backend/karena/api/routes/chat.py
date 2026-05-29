from fastapi import APIRouter, HTTPException

from karena.api.schemas import ChatRequest, ChatResponse, FeedbackRequest, SourceCitation
from karena.rag.pipeline import RAGPipeline

router = APIRouter()
_pipeline: RAGPipeline | None = None


def get_pipeline() -> RAGPipeline:
  global _pipeline
  if _pipeline is None:
    _pipeline = RAGPipeline()
  return _pipeline


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
  try:
    result = await get_pipeline().query(
      request.message,
      session_id=request.session_id,
      tenant_id=request.tenant_id,
      user_id=request.user_id,
    )
  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e)) from e

  return ChatResponse(
    answer=result.answer,
    sources=[SourceCitation(**s) for s in result.sources],
    confidence=result.confidence,
    session_id=result.session_id,
    latency_ms=round(result.latency_ms, 2),
  )


@router.post("/feedback")
async def feedback(request: FeedbackRequest):
  return {"status": "recorded", "session_id": request.session_id}
