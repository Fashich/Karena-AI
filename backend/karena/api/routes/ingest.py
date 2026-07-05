from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Request, UploadFile
from karena.api.gateway import Permission, TokenPayload, requires_permission
from karena.api.schemas import IngestResponse
from karena.config import get_settings
from karena.ingestion.etl import ingest_document
from karena.ingestion.jobs import create_job, get_job
from karena.observability.metrics import record_dlp_event
from karena.security.audit import AuditEventType, EventSeverity, get_audit_logger
from karena.security.dlp import DLPAction, get_dlp_engine
import asyncio

from karena.api.gateway import Permission, TokenPayload, requires_permission
from karena.api.schemas import IngestResponse
from karena.cache.tiers import CacheTier
from karena.config import get_settings
from karena.ingestion.etl import ingest_document
from karena.observability.metrics import record_dlp_event
from karena.security.audit import AuditEventType, EventSeverity, get_audit_logger
from karena.security.dlp import DLPAction, get_dlp_engine

router = APIRouter()


@router.post("/ingest")
async def ingest(
    request: Request,
    background_tasks: BackgroundTasks,
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

    # Create job and run as background task
    job = create_job(filename=file.filename or "document")
    asyncio.create_task(_run_ingest_job(
        job_id=job.job_id,
        filename=file.filename or "document",
        content=content,
        title=title or file.filename or "document",
        tenant_id=tenant,
    ))
    return {
        "job_id": job.job_id,
        "source_id": job.job_id,
        "chunks_indexed": 0,
        "title": title or file.filename or "document",
        "status": "processing",
    }


# ── Background ingest task ────────────────────────────────────
async def _run_ingest_job(
    job_id: str,
    filename: str,
    content: bytes,
    title: str,
    tenant_id: str,
):
    """Run document ingestion as background task with progress tracking."""
    from karena.ingestion.parser import parse_file_async
    from karena.rag.chunking import chunk_text
    from karena.rag.embeddings import get_embedding_service
    from karena.rag.vector_store import get_vector_store
    from karena.rag.hybrid_retriever import refresh_bm25_corpus
    from karena.rag.drift import get_drift_detector
    import uuid

    job = get_job(job_id)
    if not job:
        return

    try:
        settings = get_settings()
        source_id = str(uuid.uuid4())

        async def on_progress(stage: str, current: int, total: int, message: str):
            if job:
                job.stage = stage
                job.current_page = current
                job.total_pages = total
                job.message = message

        # Parse with progress
        job.status = "processing"
        job.message = "Parsing document..."
        text = await parse_file_async(filename, content, on_progress)

        # Chunk
        job.stage = "chunking"
        job.message = "Chunking text..."
        chunks = chunk_text(
            text,
            source_id=source_id,
            source_title=title,
            tenant_id=tenant_id,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            extra_metadata={"filename": filename},
        )

        if not chunks:
            job.status = "done"
            job.message = "Done — no content extracted"
            job.chunks_indexed = 0
            return

        # Embed
        job.stage = "embedding"
        job.message = f"Generating embeddings for {len(chunks)} chunks..."
        embeddings = get_embedding_service()
        loop = asyncio.get_event_loop()
        raw = await loop.run_in_executor(
            None, lambda: embeddings.embed_texts([c.text for c in chunks])
        )
        vectors = raw.tolist() if hasattr(raw, "tolist") else raw

        # Index
        job.stage = "indexing"
        job.message = "Indexing to vector store..."
        vector_store = get_vector_store()
        count = await vector_store.upsert_chunks(chunks, vectors)

        refresh_bm25_corpus(tenant_id)
        get_drift_detector().update_baseline(tenant_id, [c.text for c in chunks])

        job.status = "done"
        job.chunks_indexed = count
        job.current_page = job.total_pages or 1
        job.message = f"✅ Indexed {count} chunks successfully!"

    except Exception as e:
        if job:
            job.status = "error"
            job.error = str(e)
            job.message = f"Error: {e}"


@router.get("/ingest/progress/{job_id}")
async def ingest_progress(job_id: str):
    """Poll real-time ingestion progress."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.to_dict()

