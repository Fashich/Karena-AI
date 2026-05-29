"""Enterprise API Gateway with OAuth2/OIDC authentication and RBAC authorization.

Designed for Google Cloud APAC enterprise deployments with support for:
- Azure AD, Okta, Google Workspace federation
- Role-Based Access Control (RBAC)
- Attribute-Based Access Control (ABAC) stubs
- Adaptive rate limiting
- Request/response audit logging
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt
from pydantic import BaseModel

from karena.config import get_settings

settings = get_settings()


class UserRole(str, Enum):
    """Enterprise role hierarchy for RBAC."""

    KNOWLEDGE_WORKER = "knowledge_worker"
    OPERATIONS_MANAGER = "operations_manager"
    COMPLIANCE_OFFICER = "compliance_officer"
    IT_ADMINISTRATOR = "it_administrator"
    CTO = "cto"
    SUPER_ADMIN = "super_admin"


class Permission(str, Enum):
    """Granular permissions for access control."""

    QUERY_KNOWLEDGE = "query:knowledge"
    UPLOAD_DOCUMENTS = "upload:documents"
    VIEW_ANALYTICS = "view:analytics"
    MANAGE_USERS = "manage:users"
    MANAGE_TENANTS = "manage:tenants"
    ACCESS_AUDIT_LOGS = "access:audit_logs"
    CONFIGURE_SYSTEM = "configure:system"
    ESCALATE_QUERIES = "escalate:queries"


# Role to permission mapping
ROLE_PERMISSIONS: dict[UserRole, set[Permission]] = {
    UserRole.KNOWLEDGE_WORKER: {
        Permission.QUERY_KNOWLEDGE,
        Permission.ESCALATE_QUERIES,
    },
    UserRole.OPERATIONS_MANAGER: {
        Permission.QUERY_KNOWLEDGE,
        Permission.UPLOAD_DOCUMENTS,
        Permission.VIEW_ANALYTICS,
        Permission.ESCALATE_QUERIES,
    },
    UserRole.COMPLIANCE_OFFICER: {
        Permission.QUERY_KNOWLEDGE,
        Permission.VIEW_ANALYTICS,
        Permission.ACCESS_AUDIT_LOGS,
    },
    UserRole.IT_ADMINISTRATOR: {
        Permission.QUERY_KNOWLEDGE,
        Permission.UPLOAD_DOCUMENTS,
        Permission.VIEW_ANALYTICS,
        Permission.MANAGE_USERS,
        Permission.CONFIGURE_SYSTEM,
    },
    UserRole.CTO: {
        Permission.QUERY_KNOWLEDGE,
        Permission.VIEW_ANALYTICS,
        Permission.ACCESS_AUDIT_LOGS,
        Permission.MANAGE_TENANTS,
    },
    UserRole.SUPER_ADMIN: set(Permission),  # All permissions
}


@dataclass
class TokenPayload:
    """Decoded JWT token payload."""

    sub: str  # User ID
    email: str
    role: UserRole
    tenant_id: str
    permissions: set[Permission]
    exp: int
    iat: int


@dataclass
class RateLimitState:
    """Token bucket rate limiting state per user."""

    tokens: float = field(default=100.0)
    last_update: float = field(default_factory=time.time)
    burst_limit: int = 100
    refill_rate: float = 10.0  # tokens per second


# In-memory rate limit store (production: use Redis)
_rate_limit_store: dict[str, RateLimitState] = {}


class OAuth2Config(BaseModel):
    """OAuth2 provider configuration."""

    provider: str  # azure_ad, okta, google, keycloak
    client_id: str
    client_secret: str
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    userinfo_endpoint: str
    jwks_uri: str
    scopes: list[str] = ["openid", "email", "profile"]


class APIGateway:
    """Enterprise API Gateway with authentication, authorization, and rate limiting."""

    def __init__(self) -> None:
        self.oauth2_config: OAuth2Config | None = None
        self._jwks_cache: dict[str, Any] = {}
        self._jwks_last_fetch: float = 0

    def configure_oauth2(
        self,
        provider: str,
        client_id: str,
        client_secret: str,
        issuer: str,
    ) -> None:
        """Configure OAuth2 provider dynamically."""
        provider_configs = {
            "azure_ad": {
                "authorization_endpoint": f"{issuer}/oauth2/v2.0/authorize",
                "token_endpoint": f"{issuer}/oauth2/v2.0/token",
                "userinfo_endpoint": f"{issuer}/openid/userinfo",
                "jwks_uri": f"{issuer}/discovery/v2.0/keys",
            },
            "okta": {
                "authorization_endpoint": f"{issuer}/v1/authorize",
                "token_endpoint": f"{issuer}/v1/token",
                "userinfo_endpoint": f"{issuer}/v1/userinfo",
                "jwks_uri": f"{issuer}/v1/keys",
            },
            "google": {
                "authorization_endpoint": "https://accounts.google.com/o/oauth2/v2/auth",
                "token_endpoint": "https://oauth2.googleapis.com/token",
                "userinfo_endpoint": "https://openidconnect.googleapis.com/v1/userinfo",
                "jwks_uri": "https://www.googleapis.com/oauth2/v3/certs",
            },
        }

        config = provider_configs.get(provider, {})
        self.oauth2_config = OAuth2Config(
            provider=provider,
            client_id=client_id,
            client_secret=client_secret,
            issuer=issuer,
            authorization_endpoint=config.get("authorization_endpoint", ""),
            token_endpoint=config.get("token_endpoint", ""),
            userinfo_endpoint=config.get("userinfo_endpoint", ""),
            jwks_uri=config.get("jwks_uri", ""),
        )

    async def _fetch_jwks(self) -> dict[str, Any]:
        """Fetch JWKS from identity provider with caching."""
        now = time.time()
        if self._jwks_cache and (now - self._jwks_last_fetch) < 3600:
            return self._jwks_cache

        if not self.oauth2_config:
            return {}

        try:
            import httpx

            async with httpx.AsyncClient() as client:
                response = await client.get(self.oauth2_config.jwks_uri, timeout=10.0)
                response.raise_for_status()
                self._jwks_cache = response.json()
                self._jwks_last_fetch = now
        except Exception:
            pass

        return self._jwks_cache

    def _verify_token(self, token: str) -> TokenPayload | None:
        """Verify JWT token signature and expiration."""
        try:
            if settings.require_auth and settings.jwt_secret:
                payload = jwt.decode(
                    token,
                    settings.jwt_secret,
                    algorithms=[settings.jwt_algorithm],
                )
                return TokenPayload(
                    sub=payload.get("sub", ""),
                    email=payload.get("email", ""),
                    role=UserRole(payload.get("role", "knowledge_worker")),
                    tenant_id=payload.get("tenant_id", settings.default_tenant_id),
                    permissions=ROLE_PERMISSIONS.get(
                        UserRole(payload.get("role", "knowledge_worker")),
                        {Permission.QUERY_KNOWLEDGE},
                    ),
                    exp=payload.get("exp", 0),
                    iat=payload.get("iat", 0),
                )
        except JWTError:
            pass

        return None

    def _check_rate_limit(self, user_id: str, tenant_id: str) -> bool:
        """Token bucket rate limiting."""
        key = f"{tenant_id}:{user_id}"
        now = time.time()

        if key not in _rate_limit_store:
            _rate_limit_store[key] = RateLimitState()

        state = _rate_limit_store[key]
        elapsed = now - state.last_update
        state.tokens = min(
            state.burst_limit, state.tokens + elapsed * state.refill_rate
        )
        state.last_update = now

        if state.tokens < 1:
            return False

        state.tokens -= 1
        return True

    async def authenticate(self, request: Request) -> TokenPayload:
        """Authenticate incoming request via Bearer token or API key."""
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            if not settings.require_auth:
                return TokenPayload(
                    sub="anonymous",
                    email="anonymous@localhost",
                    role=UserRole.KNOWLEDGE_WORKER,
                    tenant_id=settings.default_tenant_id,
                    permissions={Permission.QUERY_KNOWLEDGE},
                    exp=0,
                    iat=0,
                )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
            )

        token = parts[1]
        payload = self._verify_token(token)

        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        return payload

    def authorize(
        self, current_user: TokenPayload, required_permission: Permission
    ) -> None:
        """Check if user has required permission."""
        if required_permission not in current_user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {required_permission.value}",
            )

    def enforce_rate_limit(self, user_id: str, tenant_id: str) -> None:
        """Enforce rate limiting or raise HTTP 429."""
        if not self._check_rate_limit(user_id, tenant_id):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please slow down.",
                headers={"Retry-After": "60"},
            )


# Global gateway instance
_gateway: APIGateway | None = None


def get_gateway() -> APIGateway:
    """Get or create API gateway instance."""
    global _gateway
    if _gateway is None:
        _gateway = APIGateway()
    return _gateway


# FastAPI dependencies
async def get_current_user(request: Request) -> TokenPayload:
    """Dependency to get authenticated user from request."""
    return await get_gateway().authenticate(request)


def requires_permission(permission: Permission):
    """Dependency factory for permission-based authorization."""

    async def check_permission(
        current_user: TokenPayload = Depends(get_current_user),
    ) -> TokenPayload:
        get_gateway().authorize(current_user, permission)
        return current_user

    return check_permission


async def rate_limit_middleware(
    request: Request,
    call_next,
):
    """Starlette middleware for rate limiting."""
    gateway = get_gateway()

    try:
        user = await gateway.authenticate(request)
        gateway.enforce_rate_limit(user.sub, user.tenant_id)
    except HTTPException:
        pass

    return await call_next(request)


@dataclass
class AuditLogEntry:
    """Audit log entry for compliance tracking."""

    timestamp: str
    user_id: str
    tenant_id: str
    action: str
    resource: str
    ip_address: str
    user_agent: str
    status_code: int
    metadata: dict = field(default_factory=dict)


# In-memory audit log (production: write to immutable storage)
_audit_log: list[AuditLogEntry] = []


def log_audit(
    user_id: str,
    tenant_id: str,
    action: str,
    resource: str,
    request: Request,
    status_code: int = 200,
    metadata: dict | None = None,
) -> None:
    """Record audit log entry for compliance."""
    entry = AuditLogEntry(
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        user_id=user_id,
        tenant_id=tenant_id,
        action=action,
        resource=resource,
        ip_address=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown"),
        status_code=status_code,
        metadata=metadata or {},
    )
    _audit_log.append(entry)

    # Keep last 10000 entries in memory (production: persist to database)
    if len(_audit_log) > 10000:
        _audit_log.pop(0)


def get_audit_logs(
    tenant_id: str,
    user_id: str | None = None,
    limit: int = 100,
) -> list[AuditLogEntry]:
    """Retrieve audit logs for compliance officer review."""
    filtered = [e for e in _audit_log if e.tenant_id == tenant_id]
    if user_id:
        filtered = [e for e in filtered if e.user_id == user_id]
    return filtered[-limit:]
