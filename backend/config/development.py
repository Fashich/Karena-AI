"""
Karena AI Development Configuration
Optimized for local development and testing
"""

from .settings import Settings


class DevelopmentSettings(Settings):
    """Development environment settings"""
    
    # Application
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "DEBUG"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 1  # Single worker for easier debugging
    
    # Database (local PostgreSQL)
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/karena_ai_dev"
    DATABASE_POOL_SIZE: int = 5
    
    # Redis (local)
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 300  # 5 minutes for faster iteration
    
    # Qdrant (local)
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION_NAME: str = "knowledge_base_dev"
    
    # LLM (use cheaper/faster model for dev)
    LLM_MODEL: str = "gpt-3.5-turbo"
    LLM_TEMPERATURE: float = 0.7
    
    # RAG (smaller chunks for faster testing)
    RAG_TOP_K: int = 3
    RAG_RERANK_TOP_K: int = 2
    
    # Security (simplified for dev)
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_EXPIRATION_MINUTES: int = 1440  # 24 hours
    
    # CORS (allow all local ports)
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080"
    ]
    
    # Monitoring (disabled by default in dev)
    PROMETHEUS_ENABLED: bool = False
    
    # DLP & PII (can be disabled for testing)
    DLP_ENABLED: bool = True
    PII_DETECTION_ENABLED: bool = True
    
    # Rate Limiting (relaxed for dev)
    RATE_LIMIT_REQUESTS: int = 1000
    RATE_LIMIT_WINDOW: int = 60


# Override global settings
settings = DevelopmentSettings()
