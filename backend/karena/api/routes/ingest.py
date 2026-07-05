from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile

from karena.api.gateway import Permission, TokenPayload, requires_permission
from karena.api.schemas import IngestResponse
from karena.cache.tiers import CacheTier
from karena.config import get_settings
from karena.ingestion.etl import ingest_document
from karena.observability.metrics import record_dlp_event
from karena.security.audit import AuditEventType, EventSeverity, get_audit_logger
from karena.security.dlp import DLPAction, get_dlp_engine

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse)
async def ingest(
    request: Request,
    file: UploadFile = File(...),
    title: str | None = Form(None),
    tenant_id: str | None = Form(None),
    current_user: TokenPayload = Depends(requires_permission(Permission.UPLOAD_DOCUMENTS)),
):
    content = await file.read()
    settings = get_settings()
    tenant = tenant_id or current_user.tenant_id or settings.default_tenant_id
    text_sample = content[:20000].decode("utf-8", errors="ignore")
    dlp_result = get_dlp_engine().inspect(text_sample, {"surface": "ingest"})
    audit = get_audit_logger(settings.audit_db_path)

    if dlp_result.detected_patterns:
        record_dlp_event(tenant, "document_ingest", dlp_result.recommended_action.value)
        audit.log(
            AuditEventType.DLP_VIOLATION,
            actor_id=current_user.sub,
            actor_type="user",
            action="inspect_document",
            severity=EventSeverity.WARNING,
            resource_type="document",
            resource_id=file.filename,
            details={
                "recommended_action": dlp_result.recommended_action.value,
                "detected_count": len(dlp_result.detected_patterns),
            },
            source_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            tenant_id=tenant,
            outcome="partial" if dlp_result.is_compliant else "failure",
        )

    if dlp_result.recommended_action == DLPAction.BLOCK:
        raise HTTPException(
            status_code=400,
            detail="Document blocked by DLP policy. Remove restricted secrets or identifiers before ingestion.",
        )

    result = await ingest_document(
        filename=file.filename or "document.txt",
        content=content,
        title=title,
        tenant_id=tenant,
    )

    await CacheTier().invalidate_tenant(tenant)
    audit.log(
        AuditEventType.DATA_CREATE,
        actor_id=current_user.sub,
        actor_type="user",
        action="ingest_document",
        resource_type="document",
        resource_id=result.source_id,
        details={"title": result.title, "chunks_indexed": result.chunks_indexed},
        source_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        tenant_id=tenant,
    )

    return IngestResponse(
        source_id=result.source_id,
        chunks_indexed=result.chunks_indexed,
        title=result.title,
    )

@router.post("/seed-dev", include_in_schema=False)
async def seed_dev(request: Request):
    import os
    body = await request.json()
    from karena.rag.pipeline import RAGPipeline
    pipeline = RAGPipeline()
    from karena.ingestion.etl import ingest_document
    result = await ingest_document(
        title=body.get("title", "Doc"),
        content=body.get("content", ""),
        source_id=body.get("source", "seed"),
        tenant_id=body.get("tenant_id", "default"),
    )
    return {"ok": True}
