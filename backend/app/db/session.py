import os
import time
import logging
from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, declared_attr
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import text

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create the async engine
engine = create_async_engine(settings.DATABASE_URL, echo=settings.DB_ECHO)

# Create the async session factory
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Declarative base class for models
class Base(DeclarativeBase):
    pass

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

async def get_db(request: Request = None):
    """Dependency for obtaining an async database session with tenant context."""
    async with SessionLocal() as session:
        tenant_id = None
        if request is not None:
            tenant_id = getattr(request.state, "tenant_id", None)
        if tenant_id:
            try:
                await set_tenant_context(session, str(tenant_id))
            except Exception as e:
                logger.exception(f"Failed to set app.current_tenant_id: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to bind tenant context",
                )
        yield session

async def set_tenant_context(session: AsyncSession, tenant_id: str) -> None:
    """Bind the current transaction to a tenant for PostgreSQL RLS policies."""
    await session.execute(
        text("SELECT set_config('app.bypass_rls', 'off', true)")
    )
    await session.execute(
        text("SELECT set_config('app.current_tenant_id', :tenant_id, true)"),
        {"tenant_id": tenant_id},
    )

async def enable_rls_bypass(session: AsyncSession) -> None:
    """Enable service-only RLS bypass for the current transaction."""
    await session.execute(
        text("SELECT set_config('app.bypass_rls', 'on', true)")
    )

async def check_db_health(session: AsyncSession) -> tuple[bool, float, str | None]:
    start_time = time.perf_counter()
    try:
        await session.execute(text("SELECT 1"))
        latency = (time.perf_counter() - start_time) * 1000
        return True, round(latency, 2), None
    except Exception as e:
        latency = (time.perf_counter() - start_time) * 1000
        return False, round(latency, 2), str(e)
