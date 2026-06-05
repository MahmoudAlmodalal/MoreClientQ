import contextlib
from contextvars import ContextVar
from typing import AsyncGenerator
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.config import settings

# Thread/Task-local context for the current tenant ID
tenant_context: ContextVar[str | None] = ContextVar("tenant_id", default=None)

DATABASE_URL = settings.DATABASE_URL
if DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@contextlib.contextmanager
def set_tenant_context(tenant_id: str | None):
    """Context manager to set the tenant context within a block of execution."""
    token = tenant_context.set(tenant_id)
    try:
        yield
    finally:
        tenant_context.reset(token)

@event.listens_for(AsyncSession, "after_begin")
def set_tenant_id_in_session(session, transaction, connection):
    """SQLAlchemy event listener to set app.current_tenant_id in the Postgres session.
    This ensures RLS is automatically enforced for each transaction.
    """
    tenant_id = tenant_context.get()
    if tenant_id:
        connection.execute(
            text("SELECT set_config('app.current_tenant_id', :tenant_id, true)"),
            {"tenant_id": str(tenant_id)}
        )
    else:
        # Clear/set empty if not set
        connection.execute(
            text("SELECT set_config('app.current_tenant_id', '', true)")
        )

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency to yield an async database session."""
    async with AsyncSessionLocal() as session:
        yield session
