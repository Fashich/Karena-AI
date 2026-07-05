"""Application configuration via environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Karena AI"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = True
    api_prefix: str = "/api/v1"
    api_host: str = "127.0.0.1"
    api_port: int = 8080

    # CORS
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Vector store: "memory" (no Docker) | "qdrant" (production)
    vector_store: Literal["memory", "qdrant"] = "memory"

    # Qdrant (when vector_store=qdrant)
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "karena_knowledge"
    embedding_dim: int = 384  # all-MiniLM-L6-v2

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 3600

    # Database (conversation memory)
    database_url: str = "sqlite+aiosqlite:///./data/karena.db"
    audit_db_path: str = "./data/audit.db"

    # Embeddings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    chunk_size: int = 512
    chunk_overlap: int = 64

    # Retrieval
    retrieval_top_k: int = 100
    rerank_top_k: int = 15
    hybrid_dense_weight: float = 0.7

    # LLM
    llm_provider: Literal["openai", "google", "mock"] = "mock"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = ""
    google_api_key: str = ""
    google_model: str = "gemini-2.0-flash"

    # Auth (MVP stubs)
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    require_auth: bool = False
    oauth2_provider: str | None = None
    oauth2_issuer: str | None = None
    oauth2_client_id: str | None = None
    oauth2_client_secret: str | None = None
    oauth2_redirect_uri: str | None = None
    oauth2_scope: str = "openid profile email"
    oauth2_jwks_refresh_seconds: int = 3600

    # Multi-tenancy
    default_tenant_id: str = "default"

    @property
    def auth_enabled(self) -> bool:
        return self.require_auth or bool(self.oauth2_provider and self.oauth2_issuer and self.oauth2_client_id)

    @field_validator("debug", mode="before")
    @classmethod
    def tolerate_noisy_debug_env(cls, value: object) -> object:
        if isinstance(value, str) and value.lower() not in {
            "true",
            "false",
            "1",
            "0",
            "yes",
            "no",
            "on",
            "off",
        }:
            return False
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
