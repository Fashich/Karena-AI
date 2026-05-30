from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends

from karena.agents.escalation import escalation_summary
from karena.api.gateway import Permission, TokenPayload, requires_permission
from karena.config import get_settings
from karena.memory.store import MemoryStore
from karena.rag.vector_store import get_vector_store
from karena.security.audit import AuditEventType, get_audit_logger

router = APIRouter()


@router.get("/admin/stats")
async def admin_stats(
    current_user: TokenPayload = Depends(requires_permission(Permission.VIEW_ANALYTICS)),
):
    settings = get_settings()
    try:
        info = await get_vector_store().collection_info()
        vector_ok = True
    except Exception:
        info = {}
        vector_ok = False

    feedback = await MemoryStore().feedback_summary()

    return {
        "tenant_id": current_user.tenant_id or settings.default_tenant_id,
        "environment": settings.environment,
        "vector_db": {
            "healthy": vector_ok,
            "collection": info.get("name", settings.qdrant_collection),
            "points_count": info.get("points_count", 0),
            "backend": info.get("backend", settings.vector_store),
        },
        "embedding_model": settings.embedding_model,
        "llm_provider": settings.llm_provider,
        "feedback": feedback,
        "validation_metrics": {
            "mttr_reduction_target": "30%",
            "knowledge_discovery_acceleration_target": "40%",
            "documentation_maintenance_reduction_target": "25%",
            "retrieval_precision_target": ">=85%",
            "answer_traceability_target": "100% cited responses",
        },
        "sla_targets": {
            "uptime": "99.9%",
            "p95_latency_ms": 1000,
        },
        "escalation": escalation_summary(current_user.tenant_id),
        "demo_readiness": {
            "seeded_knowledge": info.get("points_count", 0) > 0,
            "source_traceability": True,
            "human_handoff": True,
            "audit_logging": True,
            "dlp_pii_controls": True,
        },
    }


@router.get("/admin/audit")
async def audit_events(
    limit: int = 100,
    event_type: AuditEventType | None = None,
    current_user: TokenPayload = Depends(requires_permission(Permission.ACCESS_AUDIT_LOGS)),
):
    settings = get_settings()
    events = get_audit_logger(settings.audit_db_path).query_events(
        event_type=event_type,
        tenant_id=current_user.tenant_id,
        limit=min(limit, 1000),
    )
    return {"events": [event.to_dict() for event in events], "total": len(events)}


@router.get("/admin/compliance-report")
async def compliance_report(
    days: int = 30,
    current_user: TokenPayload = Depends(requires_permission(Permission.ACCESS_AUDIT_LOGS)),
):
    settings = get_settings()
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=max(1, min(days, 365)))
    report = get_audit_logger(settings.audit_db_path).generate_compliance_report(
        report_type="enterprise_access_review",
        period_start=start.isoformat(),
        period_end=end.isoformat(),
    )
    report["tenant_id"] = current_user.tenant_id
    return report
