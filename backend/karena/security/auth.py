"""Enterprise authentication and authorization module.

Supports:
- OAuth2/OIDC SSO with token validation
- API key generation, rotation, and revocation
- Session management with expiration
- Token revocation lists
- Audit logging of auth events
"""

import hashlib
import secrets
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from karena.config import get_settings
from karena.security.audit import AuditEventType, AuditEvent, EventSeverity, get_audit_logger


class APIKeyStatus(str, Enum):
    """API key lifecycle status."""

    ACTIVE = "active"
    ROTATED = "rotated"
    REVOKED = "revoked"
    EXPIRED = "expired"


@dataclass
class APIKeyRecord:
    """API key with metadata."""

    key_id: str
    key_hash: str  # SHA256 hash for storage (never store plaintext)
    tenant_id: str
    user_id: str
    status: APIKeyStatus = APIKeyStatus.ACTIVE
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_used_at: datetime | None = None
    expires_at: datetime | None = None
    rotated_at: datetime | None = None
    revoked_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_valid(self) -> bool:
        """Check if key is currently valid."""
        if self.status != APIKeyStatus.ACTIVE:
            return False
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return False
        return True

    def update_last_used(self) -> None:
        """Record when key was last used."""
        self.last_used_at = datetime.now(timezone.utc)


@dataclass
class SessionToken:
    """Represents an authenticated session."""

    session_id: str
    user_id: str
    tenant_id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime | None = None
    is_revoked: bool = False
    revoked_at: datetime | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_valid(self) -> bool:
        """Check if session is still active."""
        if self.is_revoked:
            return False
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return False
        return True


class APIKeyManager:
    """Manages API key lifecycle: generation, rotation, revocation."""

    def __init__(self) -> None:
        self._keys: dict[str, APIKeyRecord] = {}
        self._key_by_hash: dict[str, str] = {}  # hash -> key_id mapping

    def generate_key(
        self,
        user_id: str,
        tenant_id: str,
        *,
        expires_in_days: int | None = 365,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[str, APIKeyRecord]:
        """Generate a new API key.

        Returns:
            (plaintext_key, record) — plaintext key should be sent to user once,
            record stores only the hash.
        """
        key_id = str(uuid4())
        plaintext_key = f"karena_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(plaintext_key.encode()).hexdigest()

        expires_at = None
        if expires_in_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_in_days)

        record = APIKeyRecord(
            key_id=key_id,
            key_hash=key_hash,
            tenant_id=tenant_id,
            user_id=user_id,
            expires_at=expires_at,
            metadata=metadata or {},
        )

        self._keys[key_id] = record
        self._key_by_hash[key_hash] = key_id

        get_audit_logger().log(
            AuditEventType.LOGIN_SUCCESS,
            actor_id=user_id,
            actor_type="user",
            action="api_key_generated",
            resource_type="api_key",
            resource_id=key_id,
            tenant_id=tenant_id,
            details={"expires_at": expires_at.isoformat() if expires_at else None},
        )

        return plaintext_key, record

    def validate_key(self, plaintext_key: str) -> APIKeyRecord | None:
        """Validate a plaintext API key and return its record if valid."""
        key_hash = hashlib.sha256(plaintext_key.encode()).hexdigest()
        key_id = self._key_by_hash.get(key_hash)

        if not key_id:
            return None

        record = self._keys.get(key_id)
        if not record or not record.is_valid():
            return None

        record.update_last_used()
        return record

    def rotate_key(self, key_id: str) -> tuple[str, APIKeyRecord] | None:
        """Rotate an existing key, returning new plaintext key and old status updated to ROTATED."""
        record = self._keys.get(key_id)
        if not record:
            return None

        # Mark old key as rotated
        record.status = APIKeyStatus.ROTATED
        record.rotated_at = datetime.now(timezone.utc)

        # Generate new key
        new_plaintext, new_record = self.generate_key(
            user_id=record.user_id,
            tenant_id=record.tenant_id,
            expires_in_days=(
                (record.expires_at - datetime.now(timezone.utc)).days
                if record.expires_at
                else 365
            ),
            metadata=record.metadata,
        )

        get_audit_logger().log(
            AuditEventType.LOGIN_SUCCESS,
            actor_id=record.user_id,
            actor_type="user",
            action="api_key_rotated",
            resource_type="api_key",
            resource_id=key_id,
            tenant_id=record.tenant_id,
            details={"old_key_id": key_id, "new_key_id": new_record.key_id},
        )

        return new_plaintext, new_record

    def revoke_key(self, key_id: str, reason: str = "manual_revocation") -> bool:
        """Revoke an API key."""
        record = self._keys.get(key_id)
        if not record:
            return False

        record.status = APIKeyStatus.REVOKED
        record.revoked_at = datetime.now(timezone.utc)

        get_audit_logger().log(
            AuditEventType.PERMISSION_DENIED,
            actor_id=record.user_id,
            actor_type="user",
            action="api_key_revoked",
            resource_type="api_key",
            resource_id=key_id,
            tenant_id=record.tenant_id,
            details={"reason": reason},
        )

        return True

    def list_keys(self, user_id: str, tenant_id: str) -> list[APIKeyRecord]:
        """List all (active and inactive) keys for a user."""
        return [
            r
            for r in self._keys.values()
            if r.user_id == user_id and r.tenant_id == tenant_id
        ]


class SessionManager:
    """Manages authenticated sessions and token revocation."""

    def __init__(self) -> None:
        self._sessions: dict[str, SessionToken] = {}
        self._revocation_list: set[str] = set()

    def create_session(
        self,
        user_id: str,
        tenant_id: str,
        *,
        expires_in_minutes: int = 480,
        ip_address: str | None = None,
        user_agent: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SessionToken:
        """Create a new session."""
        session_id = str(uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes)

        token = SessionToken(
            session_id=session_id,
            user_id=user_id,
            tenant_id=tenant_id,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata=metadata or {},
        )

        self._sessions[session_id] = token

        get_audit_logger().log(
            AuditEventType.LOGIN_SUCCESS,
            actor_id=user_id,
            actor_type="user",
            action="session_created",
            resource_type="session",
            resource_id=session_id,
            tenant_id=tenant_id,
            source_ip=ip_address,
            user_agent=user_agent,
        )

        return token

    def validate_session(self, session_id: str) -> SessionToken | None:
        """Validate a session token."""
        token = self._sessions.get(session_id)

        if not token or not token.is_valid():
            return None

        if session_id in self._revocation_list:
            return None

        return token

    def revoke_session(self, session_id: str, reason: str = "manual_logout") -> bool:
        """Revoke a session (logout)."""
        token = self._sessions.get(session_id)
        if not token:
            return False

        token.is_revoked = True
        token.revoked_at = datetime.now(timezone.utc)
        self._revocation_list.add(session_id)

        get_audit_logger().log(
            AuditEventType.LOGOUT,
            actor_id=token.user_id,
            actor_type="user",
            action="session_revoked",
            resource_type="session",
            resource_id=session_id,
            tenant_id=token.tenant_id,
            details={"reason": reason},
        )

        return True

    def revoke_all_user_sessions(self, user_id: str, tenant_id: str, reason: str = "security_event") -> int:
        """Revoke all sessions for a user (e.g., password change)."""
        count = 0
        for session_id, token in list(self._sessions.items()):
            if token.user_id == user_id and token.tenant_id == tenant_id and token.is_valid():
                self.revoke_session(session_id, reason=reason)
                count += 1

        get_audit_logger().log(
            AuditEventType.LOGOUT,
            actor_id=user_id,
            actor_type="user",
            action="all_sessions_revoked",
            resource_type="user",
            resource_id=user_id,
            tenant_id=tenant_id,
            details={"reason": reason, "count": count},
        )

        return count


# Global singleton instances
_api_key_manager: APIKeyManager | None = None
_session_manager: SessionManager | None = None


def get_api_key_manager() -> APIKeyManager:
    """Get or create global API key manager."""
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = APIKeyManager()
    return _api_key_manager


def get_session_manager() -> SessionManager:
    """Get or create global session manager."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
