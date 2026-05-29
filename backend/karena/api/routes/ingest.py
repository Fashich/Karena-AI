from fastapi import APIRouter, File, Form, UploadFile

from karena.api.schemas import IngestResponse
from karena.cache.tiers import CacheTier
from karena.config import get_settings
from karena.ingestion.etl import ingest_document

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
async def ingest(
  file: UploadFile = File(...),
  title: str | None = Form(None),
  tenant_id: str | None = Form(None),
):
  content = await file.read()
  settings = get_settings()
  tenant = tenant_id or settings.default_tenant_id

  result = await ingest_document(
    filename=file.filename or "document.txt",
    content=content,
    title=title,
    tenant_id=tenant,
  )

  await CacheTier().invalidate_tenant(tenant)

  return IngestResponse(
    source_id=result.source_id,
    chunks_indexed=result.chunks_indexed,
    title=result.title,
  )
