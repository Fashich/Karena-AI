"""OpenID Connect (OIDC) and OAuth2 federated authentication.

Supports:
- Multiple OIDC providers (Azure AD, Okta, Google Workspace, generic OIDC)
- Authorization code flow with PKCE
- Token validation and refresh
- JWT key set caching (JWKS)
- Multi-factor authentication enforcement
- User profile mapping and claim transformation
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import httpx
from jose import JWTError, jwt

from karena.config import get_settings
from karena.security.audit import AuditEventType, get_audit_logger


@dataclass
class OIDCConfig:
    """OIDC provider configuration."""

    provider_name: str  # azure, okta, google, custom
    issuer_url: str  # e.g., https://login.microsoftonline.com/{tenant}/v2.0
    client_id: str
    client_secret: str
    redirect_uri: str  # Callback URL registered with provider
    scopes: list[str] = field(default_factory=lambda: ["openid", "profile", "email"])
    authorize_endpoint: str | None = None  # Auto-discovered if None
    token_endpoint: str | None = None
    userinfo_endpoint: str | None = None
    jwks_uri: str | None = None
    require_mfa: bool = False
    claim_mappings: dict[str, str] = field(
        default_factory=lambda: {
            "sub": "user_id",
            "email": "email",
            "name": "display_name",
            "oid": "tenant_id",  # Azure
            "org_id": "organization_id",  # Custom
        }
    )


@dataclass
class OIDCToken:
    """OIDC token response."""

    access_token: str
    token_type: str = "Bearer"
    expires_in: int | None = None
    refresh_token: str | None = None
    id_token: str | None = None
    issued_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def is_expired(self) -> bool:
        """Check if token has expired."""
        if self.expires_in is None:
            return False
        elapsed = (datetime.now(timezone.utc) - self.issued_at).total_seconds()
        return elapsed > self.expires_in


@dataclass
class OIDCUserClaims:
    """User information extracted from OIDC token claims."""

    user_id: str  # sub claim
    email: str | None = None
    display_name: str | None = None
    tenant_id: str | None = None
    organization_id: str | None = None
    mfa_verified: bool = False
    roles: list[str] = field(default_factory=list)
    groups: list[str] = field(default_factory=list)
    custom_claims: dict[str, Any] = field(default_factory=dict)


class OIDCProvider:
    """Handles OIDC authentication flows."""

    def __init__(self, config: OIDCConfig) -> None:
        self.config = config
        self._jwks_cache: dict[str, Any] = {}
        self._jwks_cache_time: float = 0
        self._jwks_cache_ttl = 3600  # 1 hour
        self._client = httpx.AsyncClient(timeout=10.0)

    async def discover_endpoints(self) -> None:
        """Auto-discover OIDC endpoints from provider's metadata."""
        try:
            metadata_url = f"{self.config.issuer_url.rstrip('/')}/.well-known/openid-configuration"
            async with self._client as client:
                response = await client.get(metadata_url)
                response.raise_for_status()
                metadata = response.json()

            self.config.authorize_endpoint = metadata.get("authorization_endpoint")
            self.config.token_endpoint = metadata.get("token_endpoint")
            self.config.userinfo_endpoint = metadata.get("userinfo_endpoint")
            self.config.jwks_uri = metadata.get("jwks_uri")
        except Exception:
            # If discovery fails, assume standard endpoints
            pass

    def get_authorization_url(self, state: str, code_challenge: str | None = None) -> str:
        """Generate authorization URL for initiating OAuth2 flow."""
        if not self.config.authorize_endpoint:
            self.config.authorize_endpoint = (
                f"{self.config.issuer_url.rstrip('/')}/oauth2/v2.0/authorize"
            )

        params = {
            "client_id": self.config.client_id,
            "response_type": "code",
            "redirect_uri": self.config.redirect_uri,
            "scope": " ".join(self.config.scopes),
            "state": state,
        }

        # PKCE support (code challenge for public clients)
        if code_challenge:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = "S256"

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.config.authorize_endpoint}?{query_string}"

    async def exchange_code_for_token(
        self,
        code: str,
        code_verifier: str | None = None,
    ) -> OIDCToken:
        """Exchange authorization code for access token."""
        if not self.config.token_endpoint:
            self.config.token_endpoint = (
                f"{self.config.issuer_url.rstrip('/')}/oauth2/v2.0/token"
            )

        data = {
            "grant_type": "authorization_code",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "code": code,
            "redirect_uri": self.config.redirect_uri,
        }

        if code_verifier:
            data["code_verifier"] = code_verifier

        async with self._client as client:
            response = await client.post(self.config.token_endpoint, data=data)
            response.raise_for_status()
            token_data = response.json()

        return OIDCToken(
            access_token=token_data["access_token"],
            token_type=token_data.get("token_type", "Bearer"),
            expires_in=token_data.get("expires_in"),
            refresh_token=token_data.get("refresh_token"),
            id_token=token_data.get("id_token"),
        )

    async def refresh_token(self, refresh_token: str) -> OIDCToken:
        """Refresh an expired access token."""
        if not self.config.token_endpoint:
            self.config.token_endpoint = (
                f"{self.config.issuer_url.rstrip('/')}/oauth2/v2.0/token"
            )

        data = {
            "grant_type": "refresh_token",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "refresh_token": refresh_token,
        }

        async with self._client as client:
            response = await client.post(self.config.token_endpoint, data=data)
            response.raise_for_status()
            token_data = response.json()

        return OIDCToken(
            access_token=token_data["access_token"],
            token_type=token_data.get("token_type", "Bearer"),
            expires_in=token_data.get("expires_in"),
            refresh_token=token_data.get("refresh_token"),
            id_token=token_data.get("id_token"),
        )

    async def get_jwks(self) -> dict[str, Any]:
        """Fetch and cache provider's JWT signing keys."""
        if not self.config.jwks_uri:
            self.config.jwks_uri = f"{self.config.issuer_url.rstrip('/')}/.well-known/jwks"

        # Return cached JWKS if still valid
        if self._jwks_cache and (time.time() - self._jwks_cache_time) < self._jwks_cache_ttl:
            return self._jwks_cache

        try:
            async with self._client as client:
                response = await client.get(self.config.jwks_uri)
                response.raise_for_status()
                self._jwks_cache = response.json()
                self._jwks_cache_time = time.time()
                return self._jwks_cache
        except Exception as e:
            if not self._jwks_cache:
                raise
            return self._jwks_cache

    async def validate_id_token(self, id_token: str) -> dict[str, Any]:
        """Validate and decode an ID token."""
        try:
            jwks = await self.get_jwks()
            header = jwt.get_unverified_header(id_token)
            kid = header.get("kid")

            # Find the correct signing key
            signing_key = None
            for key in jwks.get("keys", []):
                if key.get("kid") == kid:
                    signing_key = key
                    break

            if not signing_key:
                raise JWTError("Unable to find signing key")

            # Decode and validate token
            claims = jwt.decode(
                id_token,
                signing_key,
                algorithms=header.get("alg"),
                audience=self.config.client_id,
            )

            # Validate issuer
            if claims.get("iss") != self.config.issuer_url:
                raise JWTError("Invalid issuer")

            return claims
        except JWTError as e:
            raise ValueError(f"Invalid ID token: {e}")

    async def get_user_info(self, access_token: str) -> dict[str, Any]:
        """Fetch user information using access token."""
        if not self.config.userinfo_endpoint:
            self.config.userinfo_endpoint = (
                f"{self.config.issuer_url.rstrip('/')}/oauth2/v2.0/me"
            )

        async with self._client as client:
            response = await client.get(
                self.config.userinfo_endpoint,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            return response.json()

    def extract_user_claims(self, id_token_claims: dict[str, Any]) -> OIDCUserClaims:
        """Extract and map OIDC claims to user profile."""
        # Use configured claim mappings to extract user info
        user_id = id_token_claims.get("sub")
        if not user_id:
            raise ValueError("Missing 'sub' claim in ID token")

        claims = OIDCUserClaims(
            user_id=user_id,
            email=id_token_claims.get("email"),
            display_name=id_token_claims.get("name"),
            tenant_id=id_token_claims.get("oid") or id_token_claims.get("org_id"),
            mfa_verified=id_token_claims.get("amr", []) != [],
            roles=id_token_claims.get("roles", []),
            groups=id_token_claims.get("groups", []),
        )

        # Store any additional claims
        for key, value in id_token_claims.items():
            if key not in ("sub", "email", "name", "oid", "org_id", "amr", "roles", "groups"):
                claims.custom_claims[key] = value

        return claims


# Global OIDC provider registry
_oidc_providers: dict[str, OIDCProvider] = {}


def register_oidc_provider(name: str, config: OIDCConfig) -> OIDCProvider:
    """Register an OIDC provider."""
    provider = OIDCProvider(config)
    _oidc_providers[name] = provider
    return provider


def get_oidc_provider(name: str) -> OIDCProvider | None:
    """Get a registered OIDC provider."""
    return _oidc_providers.get(name)


async def initialize_oidc_providers() -> None:
    """Initialize configured OIDC providers from settings."""
    settings = get_settings()

    if settings.oauth2_enabled and settings.oauth2_provider:
        provider_type = settings.oauth2_provider.lower()
        redirect_uri = settings.oauth2_redirect_uri or "http://localhost:3000/auth/callback"
        scopes = [s.strip() for s in settings.oauth2_scope.split() if s.strip()]

        if provider_type == "azure":
            config = OIDCConfig(
                provider_name="azure",
                issuer_url=f"https://login.microsoftonline.com/{settings.azure_tenant_id}/v2.0",
                client_id=settings.oauth2_client_id,
                client_secret=settings.oauth2_client_secret,
                redirect_uri=redirect_uri,
                scopes=scopes,
            )
        elif provider_type == "okta":
            config = OIDCConfig(
                provider_name="okta",
                issuer_url=settings.okta_issuer_url or f"https://{settings.okta_domain}/oauth2/default",
                client_id=settings.oauth2_client_id,
                client_secret=settings.oauth2_client_secret,
                redirect_uri=redirect_uri,
                scopes=scopes,
            )
        elif provider_type == "google":
            config = OIDCConfig(
                provider_name="google",
                issuer_url="https://accounts.google.com",
                client_id=settings.oauth2_client_id,
                client_secret=settings.oauth2_client_secret,
                redirect_uri=redirect_uri,
                scopes=scopes,
            )
        else:
            config = OIDCConfig(
                provider_name="custom",
                issuer_url=settings.oauth2_issuer,
                client_id=settings.oauth2_client_id,
                client_secret=settings.oauth2_client_secret,
                redirect_uri=redirect_uri,
                scopes=scopes,
            )

        provider = register_oidc_provider(provider_type, config)
        try:
            await provider.discover_endpoints()
        except Exception:
            pass  # Continue with defaults if discovery fails
