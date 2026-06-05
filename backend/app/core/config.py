from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Database Settings
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@postgres:5432/platform"

    # Redis Settings
    REDIS_URL: str = "redis://redis:6379"

    # ChromaDB Settings
    CHROMADB_HOST: str = "chromadb"
    CHROMADB_PORT: int = 8000

    # MinIO Settings
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "admin"
    MINIO_SECRET_KEY: str = "password"

    # Security Settings
    JWT_SECRET_KEY: str = "your_jwt_secret_key_here"
    JWT_ALGORITHM: str = "HS256"
    INTERNAL_SECRET: str = "internal-service-secret"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
