import os
import time
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base, declared_attr
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import text

# PostgreSQL async database URL
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql+asyncpg://user:pass@postgres:5432/platform"
)

# Create the async engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Create the async session factory
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Declarative base class for models
Base = declarative_base()

class TenantMixin:
    """Mixin to automatically add tenant_id column with cascading deletes and indexing."""

    @declared_attr
    def tenant_id(cls):
        return Column(
            UUID(as_uuid=True),
            ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
            index=True
        )

async def get_db():
    """Dependency for obtaining an async database session."""
    async with SessionLocal() as session:
        yield session

async def check_db_health(session: AsyncSession) -> tuple[bool, float, str | None]:
    start_time = time.perf_counter()
    try:
        await session.execute(text("SELECT 1"))
        latency = (time.perf_counter() - start_time) * 1000
        return True, round(latency, 2), None
    except Exception as e:
        latency = (time.perf_counter() - start_time) * 1000
        return False, round(latency, 2), str(e)
