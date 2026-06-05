import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/moreclient_dev"
    REDIS_URL: str = "redis://localhost:6379/0"
    QDRANT_URL: str = "http://localhost:6333"
    CLAMAV_HOST: str = "localhost"
    CLAMAV_PORT: int = 3310
    JWT_SECRET: str = "your_jwt_secret_key_here_change_in_production"
    STRIPE_API_KEY: str = "sk_test_placeholder_for_billing"
    OPENAI_API_KEY: str = "sk-proj-placeholder_for_ai"
    RAG_COSINE_THRESHOLD: float = 0.75
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadminpassword"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
