"""Authentication and OIDC API routes."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from karena.api.gateway import TokenPayload, UserRole, get_current_user
from karena.config import get_settings
from karena.observability.metrics import record_auth_event, set_active_sessions
from karena.security.audit import AuditEventType, EventSeverity, get_audit_logger
from karena.security.auth import get_session_manager
from karena.security.oidc import get_oidc_provider, initialize_oidc_providers

router = APIRouter()
_oidc_state_store: dict[str, str] = {}


async def _ensure_oidc_provider(provider_name: str | None = None) -> Any:
    settings = get_settings()
    if settings.oauth2_provider and not get_oidc_provider(settings.oauth2_provider):
        await initialize_oidc_providers()

    provider = get_oidc_provider(provider_name or settings.oauth2_provider)
    if provider is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OIDC provider is not configured or unavailable.",
        )
    return provider


@router.get("/auth/providers")
async def list_oidc_providers():
    settings = get_settings()
    if not settings.oauth2_provider:
        return {"providers": []}
    return {"providers": [settings.oauth2_provider]}


@router.get("/auth/login")
async def auth_login(provider: str | None = None):
    oidc_provider = await _ensure_oidc_provider(provider)
    state = str(uuid4())
    _oidc_state_store[state] = oidc_provider.config.provider_name

    return {
        "login_url": oidc_provider.get_authorization_url(state=state),
        "state": state,
        "provider": oidc_provider.config.provider_name,
    }


@router.get("/auth/callback")
async def auth_callback(
    code: str = Query(...),
    state: str = Query(...),
    provider: str | None = Query(None),
    request: Request = None,
):
    oidc_provider = await _ensure_oidc_provider(provider)
    provider_key = _oidc_state_store.pop(state, None) or oidc_provider.config.provider_name
    if provider_key != oidc_provider.config.provider_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OIDC state and provider do not match.",
        )

    token = await oidc_provider.exchange_code_for_token(code)
    if not token.id_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ID token was not returned by the identity provider.",
        )

    claims = await oidc_provider.validate_id_token(token.id_token)
    user = oidc_provider.extract_user_claims(claims)

    if oidc_provider.config.require_mfa and not user.mfa_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Multi-factor authentication is required.",
        )

    session = get_session_manager().create_session(
        user_id=user.user_id,
        tenant_id=user.tenant_id or get_settings().default_tenant_id,
        metadata={
            "provider": oidc_provider.config.provider_name,
            "email": user.email,
            "display_name": user.display_name,
            "roles": user.roles,
        },
    )

    audit = get_audit_logger(get_settings().audit_db_path)
    audit.log(
        AuditEventType.LOGIN_SUCCESS,
        actor_id=user.user_id,
        actor_type="user",
        action="oidc_login",
        resource_type="session",
        resource_id=session.session_id,
        severity=EventSeverity.INFO,
        tenant_id=session.tenant_id,
        source_ip=request.client.host if request and request.client else None,
        user_agent=request.headers.get("user-agent") if request else None,
    )

    active_sessions = len(
        [s for s in get_session_manager()._sessions.values() if not s.is_revoked]
    )
    set_active_sessions(session.tenant_id, active_sessions)
    record_auth_event(session.tenant_id, "login_success")

    return {
        "session_id": session.session_id,
        "expires_at": session.expires_at.isoformat() if session.expires_at else None,
        "user": {
            "user_id": user.user_id,
            "email": user.email,
            "display_name": user.display_name,
            "tenant_id": user.tenant_id,
            "roles": user.roles,
        },
        "access_token": token.access_token,
        "refresh_token": token.refresh_token,
    }


@router.post("/auth/refresh")
async def auth_refresh(refresh_token: str = Query(...), provider: str | None = Query(None)):
    oidc_provider = await _ensure_oidc_provider(provider)
    refreshed = await oidc_provider.refresh_token(refresh_token)
    return {
        "access_token": refreshed.access_token,
        "refresh_token": refreshed.refresh_token,
        "expires_in": refreshed.expires_in,
    }


@router.post("/auth/logout")
async def auth_logout(
    session_id: str,
    current_user: TokenPayload = Depends(get_current_user),
):
    session_manager = get_session_manager()
    session = session_manager.validate_session(session_id)
    if not session or session.user_id != current_user.sub:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot revoke session for a different user.",
        )

    session_manager.revoke_session(session_id)
    record_auth_event(current_user.tenant_id, "logout")
    active_sessions = len([s for s in session_manager._sessions.values() if not s.is_revoked])
    set_active_sessions(current_user.tenant_id, active_sessions)
    return {"status": "logged_out", "session_id": session_id}


@router.get("/auth/session/{session_id}")
async def get_session_status(
    session_id: str,
    current_user: TokenPayload = Depends(get_current_user),
):
    session = get_session_manager().validate_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.user_id != current_user.sub and current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    return {
        "session_id": session.session_id,
        "user_id": session.user_id,
        "tenant_id": session.tenant_id,
        "expires_at": session.expires_at.isoformat() if session.expires_at else None,
        "metadata": session.metadata,
        "is_revoked": session.is_revoked,
    }
