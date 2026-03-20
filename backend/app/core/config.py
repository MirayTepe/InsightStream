"""Application configuration via Pydantic Settings."""

from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    project_name: str = "InsightStream"
    api_v1_prefix: str = "/api/v1"
    environment: str = Field(default="dev", description="dev | staging | prod")
    debug: bool = Field(default=False, description="Enable debug mode")
    max_upload_size_mb: int = Field(default=50, description="Max PDF upload size in MB")

    # CORS
    backend_cors_origins: List[AnyHttpUrl] = Field(
        default_factory=lambda: [],
        description="Allowed CORS origins (empty = defaults in code)",
    )

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/insightstream",
        description="PostgreSQL connection URL",
    )
    database_url_sync: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/insightstream",
        description="Synchronous PostgreSQL URL for Alembic/SQLAlchemy sync",
    )

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for cache and Celery result backend",
    )

    # RabbitMQ
    rabbitmq_url: str = Field(
        default="amqp://guest:guest@localhost:5672//",
        description="RabbitMQ connection URL for Celery broker",
    )

    # JWT / Auth
    jwt_secret_key: str = Field(
        default="change-me-in-production-use-openssl-rand-hex-32",
        description="Secret key for JWT signing",
    )
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # Google Cloud / Vertex AI
    gcp_project_id: str = Field(default="your-gcp-project-id", description="GCP project ID")
    gcp_location: str = Field(default="us-central1", description="Vertex AI region")
    vertex_text_embedding_model: str = "text-embedding-004"
    vertex_flash_model: str = "gemini-1.5-flash-001"
    vertex_pro_model: str = "gemini-1.5-pro-001"

    # Gemini API key (ai.google.dev / Google AI Studio).
    # When set, the app will prefer API-key based Gemini generation over Vertex AI (ADC).
    google_api_key: str = Field(default="", description="Gemini API key for API-key based access")

    # Gemini API-key embeddings model id.
    # These are used with the `google.genai` SDK when `GOOGLE_API_KEY` is provided.
    gemini_embedding_model: str = Field(
        default="models/gemini-embedding-2-preview",
        description="Gemini API embeddings model id for API-key based embedding",
    )

    # Text-to-Speech
    tts_voice_name: str = "en-US-Neural2-C"
    tts_language_code: str = "en-US"

    # RAG
    rag_default_top_k: int = 5
    rag_chunk_size: int = 800
    rag_chunk_overlap: int = 200

    # Vector storage
    vector_store_type: str = Field(
        default="faiss",
        description="faiss | pinecone | weaviate | chroma",
    )
    faiss_index_path: str = Field(default="./data/faiss", description="Local FAISS index directory")

    # Storage (file)
    storage_type: str = Field(default="local", description="local | s3")
    storage_local_path: str = Field(default="./data/uploads", description="Local upload directory")
    s3_bucket_name: str = Field(default="", description="S3 bucket when storage_type=s3")

    # Rate limiting
    rate_limit_requests_per_minute: int = 60
    rate_limit_enabled: bool = True

    # Observability
    prometheus_enabled: bool = True
    log_level: str = Field(default="INFO", description="logging level")

    @property
    def max_upload_bytes(self) -> int:
        """Max upload size in bytes."""
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()


settings = get_settings()
