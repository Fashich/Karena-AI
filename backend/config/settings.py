"""
Karena AI Application Settings
Centralized configuration management for all environments
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings with environment variable overrides"""
    
    # Application
    APP_NAME: str = "Karena AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/karena_ai",
        description="PostgreSQL connection string"
    )
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection string"
    )
    REDIS_CACHE_TTL: int = 3600  # 1 hour
    
    # Qdrant Vector Database
    QDRANT_URL: str = Field(
        default="http://localhost:6333",
        description="Qdrant vector database URL"
    )
    QDRANT_COLLECTION_NAME: str = "knowledge_base"
    EMBEDDING_DIMENSION: int = 768
    
    # Embedding Models
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_BATCH_SIZE: int = 32
    
    # LLM Configuration
    LLM_PROVIDER: str = "openai"  # openai, anthropic, local
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 2048
    LLM_API_KEY: Optional[str] = None
    
    # RAG Configuration
    RAG_TOP_K: int = 5
    RAG_RERANK_TOP_K: int = 3
    RAG_CHUNK_SIZE: int = 512
    RAG_CHUNK_OVERLAP: int = 50
    RAG_CONFIDENCE_THRESHOLD: float = 0.7
    
    # Security
    SECRET_KEY: str = Field(
        default="change-me-in-production",
        description="Secret key for JWT and encryption"
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60
    API_KEY_PREFIX: str = "karena_"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "https://app.karena.ai"
    ]
    
    # Monitoring
    PROMETHEUS_ENABLED: bool = True
    PROMETHEUS_PORT: int = 9090
    OTEL_EXPORTER_OTLP_ENDPOINT: Optional[str] = None
    LOG_LEVEL: str = "INFO"
    
    # File Storage
    UPLOAD_DIR: str = "/tmp/karena_uploads"
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_FILE_TYPES: List[str] = [
        ".pdf", ".docx", ".txt", ".md", 
        ".csv", ".xlsx", ".pptx"
    ]
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # A/B Testing
    AB_TESTING_ENABLED: bool = True
    
    # DLP & PII
    DLP_ENABLED: bool = True
    PII_DETECTION_ENABLED: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get settings instance for dependency injection"""
    return settings
