import os
# Hot-fix for docker daemon zombie redis container port conflict
if os.getenv("REDIS_URL") == "redis://redis:6379":
    os.environ["REDIS_URL"] = "redis://redis-service:6379"

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Database Settings
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@postgres:5432/platform"
    DB_ECHO: bool = False

    # Redis Settings
    REDIS_URL: str = "redis://127.0.0.1:6379"

    # ChromaDB Settings
    CHROMADB_HOST: str = "chromadb"
    CHROMADB_PORT: int = 8000

    # MinIO Settings
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "admin"
    MINIO_SECRET_KEY: str = "password"
    MINIO_SECURE: bool = False
    MINIO_BUCKET_NAME: str = "platform-documents"

    # Security Settings
    JWT_SECRET_KEY: str = "your_jwt_secret_key_here"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    INTERNAL_SECRET: str = "internal-service-secret"
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 100

    # CORS Settings
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://platform.localhost:3000",
    ]
    ALLOWED_ORIGIN_REGEX: str | None = "http://.*\\.localhost:3000"

    # Public widget asset origin used in assistant embed snippets.
    WIDGET_BASE_URL: str = "https://platform.com"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
