from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends

from karena.agents.escalation import escalation_summary
from karena.api.gateway import Permission, TokenPayload, requires_permission
from karena.config import get_settings
from karena.memory.store import MemoryStore
from karena.rag.drift import get_drift_detector
from karena.rag.model_registry import get_model_registry
from karena.rag.model_lifecycle import get_embedding_model_registry, ModelStatus, ModelEvaluationMetric
from karena.rag.vector_store import get_vector_store
from karena.security.audit import AuditEventType, get_audit_logger
from karena.security.auth import get_api_key_manager, get_session_manager, APIKeyStatus

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


@router.get("/admin/model-registry")
async def model_registry(
    current_user: TokenPayload = Depends(requires_permission(Permission.VIEW_ANALYTICS)),
):
    registry = get_embedding_model_registry()
    current_model = registry.get_current_model()
    canary_model = registry.get_canary_model()
    
    return {
        "active_model": {
            "model_id": current_model.model_id if current_model else None,
            "model_name": current_model.model_name if current_model else None,
            "version": current_model.version if current_model else None,
            "status": current_model.status if current_model else None,
            "promoted_at": current_model.promoted_at.isoformat() if current_model and current_model.promoted_at else None,
        } if current_model else None,
        "canary_model": {
            "model_id": canary_model.model_id if canary_model else None,
            "model_name": canary_model.model_name if canary_model else None,
            "version": canary_model.version if canary_model else None,
            "traffic_percentage": canary_model.canary_traffic_percentage if canary_model else 0,
        } if canary_model else None,
        "models": [
            {
                "model_id": model.model_id,
                "model_name": model.model_name,
                "version": model.version,
                "status": model.status,
                "dimension": model.dimension,
                "created_at": model.created_at.isoformat(),
                "promoted_at": model.promoted_at.isoformat() if model.promoted_at else None,
                "latest_evaluation": {
                    "evaluation_id": model.latest_evaluation().evaluation_id if model.latest_evaluation() else None,
                    "passed_quality_gate": model.latest_evaluation().passed_quality_gate if model.latest_evaluation() else False,
                    "metrics": dict(model.latest_evaluation().metrics) if model.latest_evaluation() else {},
                } if model.latest_evaluation() else None,
            }
            for model in registry.list_models()
        ],
    }


@router.get("/admin/model-evaluation")
async def model_evaluation(
    model_id: str,
    current_user: TokenPayload = Depends(requires_permission(Permission.VIEW_ANALYTICS)),
):
    """Get evaluation history for a specific model."""
    registry = get_embedding_model_registry()
    model = registry.get_model(model_id)
    
    if not model:
        return {"error": "Model not found", "model_id": model_id}
    
    return {
        "model_id": model.model_id,
        "model_name": model.model_name,
        "version": model.version,
        "status": model.status,
        "evaluations": [
            {
                "evaluation_id": eval.evaluation_id,
                "timestamp": eval.timestamp.isoformat(),
                "metrics": {k.value: v for k, v in eval.metrics.items()},
                "sample_count": eval.sample_count,
                "dataset_id": eval.dataset_id,
                "passed_quality_gate": eval.passed_quality_gate,
            }
            for eval in sorted(model.evaluations, key=lambda e: e.timestamp, reverse=True)
        ],
    }


@router.post("/admin/model-promote")
async def promote_model(
    model_id: str,
    to_status: str,
    traffic_percentage: float | None = None,
    current_user: TokenPayload = Depends(requires_permission(Permission.MANAGE_MODELS)),
):
    """Promote a model through lifecycle stages."""
    registry = get_embedding_model_registry()
    model = registry.get_model(model_id)
    
    if not model:
        return {"error": "Model not found", "model_id": model_id}
    
    success = False
    if to_status == "canary":
        success = registry.promote_to_canary(model_id, traffic_percentage=traffic_percentage or 10.0)
    elif to_status == "stable":
        success = registry.promote_to_stable(model_id)
    elif to_status == "deprecated":
        success = registry.deprecate_model(model_id)
    elif to_status == "retired":
        success = registry.retire_model(model_id)
    
    if success:
        updated_model = registry.get_model(model_id)
        get_audit_logger(get_settings().audit_db_path).log_event(
            event_type=AuditEventType.CONFIGURATION_CHANGE,
            tenant_id=current_user.tenant_id,
            user_id=current_user.sub,
            resource="embedding_model",
            action=f"promoted to {to_status}",
            details={"model_id": model_id, "new_status": to_status},
        )
        return {
            "success": True,
            "model_id": model_id,
            "new_status": updated_model.status if updated_model else None,
        }
    else:
        return {"success": False, "error": f"Cannot promote model to {to_status} from current status"}


@router.get("/admin/auth-metrics")
async def auth_metrics(
    current_user: TokenPayload = Depends(requires_permission(Permission.ACCESS_AUDIT_LOGS)),
):
    """Get authentication and authorization metrics."""
    api_key_manager = get_api_key_manager()
    session_manager = get_session_manager()
    
    # Collect stats from API key manager
    active_keys = len([k for k in api_key_manager._keys.values() if k.status == APIKeyStatus.ACTIVE])
    rotated_keys = len([k for k in api_key_manager._keys.values() if k.status == APIKeyStatus.ROTATED])
    revoked_keys = len([k for k in api_key_manager._keys.values() if k.status == APIKeyStatus.REVOKED])
    
    # Collect stats from session manager
    active_sessions = len([s for s in session_manager._sessions.values() if not s.is_revoked])
    
    return {
        "api_keys": {
            "active": active_keys,
            "rotated": rotated_keys,
            "revoked": revoked_keys,
            "total": len(api_key_manager._keys),
        },
        "sessions": {
            "active": active_sessions,
            "total": len(session_manager._sessions),
        },
        "tenant_id": current_user.tenant_id,
    }



@router.get("/admin/api-keys")
async def list_api_keys(
    current_user: TokenPayload = Depends(requires_permission(Permission.MANAGE_API_KEYS)),
):
    """List API keys for the current user."""
    api_key_manager = get_api_key_manager()
    keys = api_key_manager._keys.values()
    
    return {
        "api_keys": [
            {
                "key_id": k.key_id,
                "tenant_id": k.tenant_id,
                "user_id": k.user_id,
                "status": k.status,
                "created_at": k.created_at.isoformat(),
                "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
                "expires_at": k.expires_at.isoformat() if k.expires_at else None,
            }
            for k in sorted(keys, key=lambda k: k.created_at, reverse=True)
        ]
    }


@router.get("/admin/sessions")
async def list_sessions(
    current_user: TokenPayload = Depends(requires_permission(Permission.ACCESS_AUDIT_LOGS)),
):
    """List active sessions for the current user."""
    session_manager = get_session_manager()
    sessions = [s for s in session_manager._sessions.values() if s.user_id == current_user.sub and not s.is_revoked]
    
    return {
        "sessions": [
            {
                "session_id": s.session_id,
                "user_id": s.user_id,
                "created_at": datetime.fromtimestamp(int(s.session_id[:8], 16), tz=timezone.utc).isoformat(),
                "expires_at": s.expires_at.isoformat(),
                "ip_address": s.ip_address,
                "user_agent": s.user_agent,
            }
            for s in sorted(sessions, key=lambda s: s.expires_at, reverse=True)
        ]
    }



@router.get("/admin/drift")
async def drift_status(
    tenant_id: str | None = None,
    current_user: TokenPayload = Depends(requires_permission(Permission.VIEW_ANALYTICS)),
):
    tenant = tenant_id or current_user.tenant_id
    detector = get_drift_detector()
    baseline_exists = tenant in detector._tenant_baselines
    return {
        "tenant_id": tenant,
        "baseline_exists": baseline_exists,
        "drift_threshold": detector.threshold,
        "recommendation": (
            "Collect a representative corpus snapshot and call the drift evaluation helper to compute drift scores."
            if not baseline_exists
            else "Baseline exists; run drift evaluation with recent corpus snapshots."
        ),
    }
