import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Declare Base for testing setup if models are not imported yet
Base = declarative_base()

# SQLite async in-memory database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create session-wide async engine for testing."""
    engine = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    
    # In a real environment, we'd import models and do Base.metadata.create_all
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide an isolated database session per test case."""
    AsyncSessionLocal = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()

@pytest.fixture
def make_tenant():
    """Factory fixture to create dummy tenant configurations for tests."""
    def _make(tenant_id: str, name: str = "Test Tenant", region: str = "GCC"):
        return {
            "id": tenant_id,
            "name": name,
            "region": region,
            "status": "active"
        }
    return _make

@pytest.fixture
def set_rls_context():
    """Helper fixture to set the tenant RLS context on a session."""
    async def _set(session: AsyncSession, tenant_id: str):
        # Executes SQLite-compatible parameter setting or mocks Postgres SET LOCAL
        # SQLite doesn't have SET LOCAL, so we can mock or execute a custom function if needed
        # For SQLite tests, we can execute: select 1; to simulate setting RLS variable
        await session.execute(Base.metadata.bind.execute(f"# Mock SET LOCAL app.current_tenant_id = '{tenant_id}'") if hasattr(Base.metadata.bind, 'execute') else "SELECT 1")
    return _set

@pytest_asyncio.fixture
async def client() -> AsyncGenerator[object, None]:
    """HTTPX async client fixture for API endpoint testing."""
    # Dummy mock client until FastAPI app is created in Phase 2
    # In Phase 2, this will import from src.main import app and wrap with AsyncClient
    from httpx import AsyncClient
    async with AsyncClient(base_url="http://testserver") as ac:
        yield ac
