"""
Karena AI Production Configuration
Optimized for production deployment with security and performance
"""

import os
from .settings import Settings


class ProductionSettings(Settings):
    """Production environment settings"""

    # Application
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    LOG_LEVEL: str = "WARNING"

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4  # Multiple workers for production

    # Database (production PostgreSQL with credentials from env)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "postgresql://postgres:secure-password@db.production.svc:5432/karena_ai"
    )
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 40

    # Redis (production cluster)
    REDIS_URL: str = os.getenv(
        "REDIS_URL", "redis://:secure-redis-password@redis.production.svc:6379/0"
    )
    REDIS_CACHE_TTL: int = 7200  # 2 hours

    # Qdrant (production cluster)
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://qdrant.production.svc:6333")
    QDRANT_COLLECTION_NAME: str = "knowledge_base_prod"

    # LLM (production-grade model)
    LLM_MODEL: str = "gpt-4o"
    LLM_TEMPERATURE: float = 0.5  # More deterministic for production

    # RAG (higher quality retrieval)
    RAG_TOP_K: int = 10
    RAG_RERANK_TOP_K: int = 5
    RAG_CONFIDENCE_THRESHOLD: float = 0.8

    # Security (strong security settings)
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    if not SECRET_KEY or SECRET_KEY == "change-me-in-production":
        raise ValueError("SECRET_KEY must be set in production")

    JWT_ALGORITHM: str = "RS256"  # Use asymmetric keys in production
    JWT_EXPIRATION_MINUTES: int = 30  # Shorter token lifetime

    # CORS (restrict to production domains only)
    CORS_ORIGINS: list = ["https://app.karena.ai", "https://platform.karena.ai"]

    # Monitoring (enabled in production)
    PROMETHEUS_ENABLED: bool = True
    OTEL_EXPORTER_OTLP_ENDPOINT: str = os.getenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector.monitoring.svc:4317"
    )

    # File Storage (persistent storage)
    UPLOAD_DIR: str = "/var/data/karena_uploads"

    # Rate Limiting (stricter in production)
    RATE_LIMIT_REQUESTS: int = 60
    RATE_LIMIT_WINDOW: int = 60

    # DLP & PII (always enabled in production)
    DLP_ENABLED: bool = True
    PII_DETECTION_ENABLED: bool = True

    # A/B Testing (enabled for optimization)
    AB_TESTING_ENABLED: bool = True


# Override global settings
settings = ProductionSettings()
