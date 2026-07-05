from fastapi import APIRouter, Depends, HTTPException, Request

from karena.api.gateway import Permission, TokenPayload, requires_permission
from karena.api.schemas import (
    ChatRequest,
    ChatResponse,
    FeedbackRequest,
    SourceCitation,
)
from karena.config import get_settings
from karena.memory.store import MemoryStore
from karena.observability.metrics import record_dlp_event, record_feedback
from karena.rag.pipeline import RAGPipeline
from karena.security.audit import AuditEventType, EventSeverity, get_audit_logger
from karena.security.dlp import DLPAction, get_dlp_engine
from karena.security.pii import get_pii_detector

router = APIRouter()
_pipeline: RAGPipeline | None = None


def get_pipeline() -> RAGPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = RAGPipeline()
    return _pipeline


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request_body: ChatRequest,
    request: Request,
    current_user: TokenPayload = Depends(requires_permission(Permission.QUERY_KNOWLEDGE)),
):
    settings = get_settings()
    tenant_id = request_body.tenant_id or current_user.tenant_id or settings.default_tenant_id
    user_id = request_body.user_id if request_body.user_id != "anonymous" else current_user.sub
    audit = get_audit_logger(settings.audit_db_path)
    source_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    message = request_body.message
    dlp_result = get_dlp_engine().inspect(message, {"surface": "chat"})
    pii_result = get_pii_detector().detect(message)

    if dlp_result.detected_patterns or pii_result.has_pii:
        action = dlp_result.recommended_action.value
        if pii_result.has_pii and action == DLPAction.ALLOW.value:
            action = pii_result.recommended_action
        record_dlp_event(tenant_id, "chat_request", action)
        audit.log(
            AuditEventType.DLP_VIOLATION
            if not dlp_result.is_compliant
            else AuditEventType.PII_DETECTED,
            actor_id=user_id,
            actor_type="user",
            action="inspect_chat_query",
            severity=EventSeverity.WARNING,
            resource_type="chat",
            details={
                "dlp_action": dlp_result.recommended_action.value,
                "pii_action": pii_result.recommended_action,
                "pii_categories": [c.value for c in pii_result.categories_found],
            },
            source_ip=source_ip,
            user_agent=user_agent,
            tenant_id=tenant_id,
            session_id=request_body.session_id,
            outcome="partial" if dlp_result.is_compliant else "failure",
        )

    if dlp_result.recommended_action == DLPAction.BLOCK:
        raise HTTPException(
            status_code=400,
            detail="Query blocked by DLP policy. Remove restricted secrets or identifiers and try again.",
        )

    if dlp_result.redacted_content:
        message = dlp_result.redacted_content
    elif pii_result.masked_content and pii_result.recommended_action in {"redact", "block_or_redact"}:
        message = pii_result.masked_content

    # ── Web search augmentation ───────────────────────────────
    web_search_enabled = getattr(request_body, "web_search", False)
    if web_search_enabled:
        try:
            from karena.search.web_search import WebSearchService
            svc = WebSearchService(tavily_api_key=settings.tavily_api_key)
            web_results = await svc.search(message, max_results=4)
            if web_results:
                web_context = svc.format_for_llm(web_results, message)
                message = web_context + "\n\nUser question: " + message
        except Exception as _web_err:
            import logging
            logging.getLogger(__name__).warning("Web search failed: %s", _web_err)

    try:
        result = await get_pipeline().query(
            message,
            session_id=request_body.session_id,
            tenant_id=tenant_id,
            user_id=user_id,
        )
    except Exception as e:
        audit.log(
            AuditEventType.RAG_QUERY,
            actor_id=user_id,
            actor_type="user",
            action="chat_query",
            severity=EventSeverity.ERROR,
            resource_type="chat",
            source_ip=source_ip,
            user_agent=user_agent,
            tenant_id=tenant_id,
            session_id=request_body.session_id,
            outcome="failure",
            error_message=str(e),
        )
        raise HTTPException(status_code=500, detail=str(e)) from e

    response_dlp = get_dlp_engine().inspect(result.answer, {"surface": "chat_response"})
    response_pii = get_pii_detector().detect(result.answer)
    answer = result.answer
    if response_dlp.redacted_content:
        answer = response_dlp.redacted_content
    elif response_pii.masked_content and response_pii.recommended_action in {
        "redact",
        "block_or_redact",
    }:
        answer = response_pii.masked_content

    audit.log(
        AuditEventType.RAG_QUERY,
        actor_id=user_id,
        actor_type="user",
        action="chat_query",
        resource_type="chat",
        details={
            "confidence": result.confidence,
            "latency_ms": result.latency_ms,
            "sources": len(result.sources),
            "trace_id": result.trace.get("trace_id"),
            "web_search": web_search_enabled,
        },
        source_ip=source_ip,
        user_agent=user_agent,
        tenant_id=tenant_id,
        session_id=result.session_id,
    )

    return ChatResponse(
        answer=answer,
        sources=[SourceCitation(**s) for s in result.sources],
        confidence=result.confidence,
        session_id=result.session_id,
        latency_ms=round(result.latency_ms, 2),
    )


@router.post("/feedback")
async def feedback(
    request_body: FeedbackRequest,
    request: Request,
    current_user: TokenPayload = Depends(requires_permission(Permission.QUERY_KNOWLEDGE)),
):
    settings = get_settings()
    feedback_id = await MemoryStore().add_feedback(
        request_body.session_id,
        request_body.rating,
        comment=request_body.comment,
    )
    record_feedback(request_body.rating, current_user.tenant_id)
    get_audit_logger(settings.audit_db_path).log(
        AuditEventType.DATA_CREATE,
        actor_id=current_user.sub,
        actor_type="user",
        action="submit_feedback",
        resource_type="feedback",
        resource_id=feedback_id,
        details={"rating": request_body.rating},
        source_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        tenant_id=current_user.tenant_id,
        session_id=request_body.session_id,
    )
    return {
        "status": "recorded",
        "feedback_id": feedback_id,
        "session_id": request_body.session_id,
    }
