import uuid
import pytest
import pytest_asyncio
from sqlalchemy import text, update
from sqlalchemy.future import select

from app.db.session import SessionLocal
from app.models.tenant import Tenant
from app.models.user import User
from app.core.security import get_password_hash


async def _seed_data():
    """Create two tenants each with one user for RLS isolation testing."""
    async with SessionLocal() as session:
        tenant_a = Tenant(
            slug="tenant-a",
            name="Tenant A",
            plan="starter",
            is_active=True,
            settings={},
            monthly_quota=1000,
            used_quota=0,
        )
        tenant_b = Tenant(
            slug="tenant-b",
            name="Tenant B",
            plan="starter",
            is_active=True,
            settings={},
            monthly_quota=1000,
            used_quota=0,
        )
        session.add_all([tenant_a, tenant_b])
        await session.flush()

        user_a = User(
            tenant_id=tenant_a.id,
            email="user_a@test.com",
            hashed_password=get_password_hash("password"),
            role="admin",
            is_active=True,
        )
        user_b = User(
            tenant_id=tenant_b.id,
            email="user_b@test.com",
            hashed_password=get_password_hash("password"),
            role="member",
            is_active=True,
        )
        session.add_all([user_a, user_b])
        await session.commit()

        return {
            "tenant_a_id": str(tenant_a.id),
            "tenant_b_id": str(tenant_b.id),
            "user_a_id": str(user_a.id),
            "user_b_id": str(user_b.id),
        }


async def _cleanup():
    async with SessionLocal() as session:
        await session.execute(text("TRUNCATE TABLE users, tenants CASCADE"))
        await session.commit()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    await _cleanup()
    data = await _seed_data()
    yield data
    await _cleanup()


@pytest.mark.asyncio
async def test_rls_isolation_tenant_a_cannot_see_tenant_b(setup_db):
    """Tenant A session should only see users belonging to Tenant A."""
    async with SessionLocal() as session:
        await session.execute(
            text(f"SET LOCAL app.current_tenant_id = '{setup_db['tenant_a_id']}'")
        )
        result = await session.execute(select(User).order_by(User.email))
        users = result.scalars().all()

        assert len(users) == 1
        assert users[0].email == "user_a@test.com"


@pytest.mark.asyncio
async def test_rls_isolation_tenant_b_cannot_see_tenant_a(setup_db):
    """Tenant B session should only see users belonging to Tenant B."""
    async with SessionLocal() as session:
        await session.execute(
            text(f"SET LOCAL app.current_tenant_id = '{setup_db['tenant_b_id']}'")
        )
        result = await session.execute(select(User).order_by(User.email))
        users = result.scalars().all()

        assert len(users) == 1
        assert users[0].email == "user_b@test.com"


@pytest.mark.asyncio
async def test_rls_no_tenant_context_returns_no_rows(setup_db):
    """Without setting app.current_tenant_id, RLS should filter out all rows."""
    async with SessionLocal() as session:
        result = await session.execute(select(User).order_by(User.email))
        users = result.scalars().all()

        assert len(users) == 0


@pytest.mark.asyncio
async def test_rls_bypass_with_set_tenant_id(setup_db):
    """Setting the tenant context allows seeing that tenant's rows."""
    async with SessionLocal() as session:
        await session.execute(
            text(f"SET LOCAL app.current_tenant_id = '{setup_db['tenant_a_id']}'")
        )
        result = await session.execute(select(User))
        users_a = result.scalars().all()
        tenant_a_emails = [u.email for u in users_a]

    async with SessionLocal() as session:
        await session.execute(
            text(f"SET LOCAL app.current_tenant_id = '{setup_db['tenant_b_id']}'")
        )
        result = await session.execute(select(User))
        users_b = result.scalars().all()
        tenant_b_emails = [u.email for u in users_b]

    assert "user_a@test.com" in tenant_a_emails
    assert "user_b@test.com" not in tenant_a_emails
    assert "user_b@test.com" in tenant_b_emails
    assert "user_a@test.com" not in tenant_b_emails


@pytest.mark.asyncio
async def test_rls_insert_with_tenant_context(setup_db):
    """Inserting a user within a tenant context should succeed."""
    async with SessionLocal() as session:
        await session.execute(
            text(f"SET LOCAL app.current_tenant_id = '{setup_db['tenant_a_id']}'")
        )

        new_user = User(
            id=uuid.uuid4(),
            tenant_id=uuid.UUID(setup_db["tenant_a_id"]),
            email="new_user_a@test.com",
            hashed_password=get_password_hash("password"),
            role="member",
            is_active=True,
        )
        session.add(new_user)
        await session.commit()

    async with SessionLocal() as session:
        await session.execute(
            text(f"SET LOCAL app.current_tenant_id = '{setup_db['tenant_a_id']}'")
        )
        result = await session.execute(
            select(User).where(User.email == "new_user_a@test.com")
        )
        user = result.scalar_one_or_none()
        assert user is not None
        assert user.email == "new_user_a@test.com"


@pytest.mark.asyncio
async def test_rls_update_within_tenant(setup_db):
    """Updating a user row within the correct tenant context should succeed."""
    async with SessionLocal() as session:
        await session.execute(
            text(f"SET LOCAL app.current_tenant_id = '{setup_db['tenant_a_id']}'")
        )
        await session.execute(
            update(User)
            .where(User.email == "user_a@test.com")
            .values(full_name="Updated User A")
        )
        await session.commit()

    async with SessionLocal() as session:
        await session.execute(
            text(f"SET LOCAL app.current_tenant_id = '{setup_db['tenant_a_id']}'")
        )
        result = await session.execute(
            select(User).where(User.email == "user_a@test.com")
        )
        user = result.scalar_one()
        assert user.full_name == "Updated User A"
