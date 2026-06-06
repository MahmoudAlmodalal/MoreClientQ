import uuid
import pytest
import pytest_asyncio
from sqlalchemy import text, update
from sqlalchemy.future import select

from app.db.session import SessionLocal
from app.db.session import enable_rls_bypass
from app.models.tenant import Tenant
from app.models.user import User
from app.models.assistant import Assistant
from app.models.document import Document
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.quota_log import QuotaLog
from app.models.invitation import Invitation
from app.core.security import get_password_hash
from datetime import datetime, timedelta, timezone


async def _seed_data():
    """Create two tenants each with one user for RLS isolation testing."""
    async with SessionLocal() as session:
        await enable_rls_bypass(session)
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
        assistant_a = Assistant(tenant_id=tenant_a.id, name="Assistant A")
        assistant_b = Assistant(tenant_id=tenant_b.id, name="Assistant B")
        session.add_all([assistant_a, assistant_b])
        await session.flush()

        document_a = Document(
            tenant_id=tenant_a.id,
            assistant_id=assistant_a.id,
            filename="a.txt",
            storage_key="tenant-a/a.txt",
            file_type="text/plain",
            status="ready",
        )
        document_b = Document(
            tenant_id=tenant_b.id,
            assistant_id=assistant_b.id,
            filename="b.txt",
            storage_key="tenant-b/b.txt",
            file_type="text/plain",
            status="ready",
        )
        conversation_a = Conversation(
            tenant_id=tenant_a.id,
            assistant_id=assistant_a.id,
            session_token="session-a",
        )
        conversation_b = Conversation(
            tenant_id=tenant_b.id,
            assistant_id=assistant_b.id,
            session_token="session-b",
        )
        quota_a = QuotaLog(tenant_id=tenant_a.id, resource="messages", amount=1)
        quota_b = QuotaLog(tenant_id=tenant_b.id, resource="messages", amount=2)
        invitation_a = Invitation(
            tenant_id=tenant_a.id,
            email="invite_a@test.com",
            role="member",
            token="invite-a",
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        )
        invitation_b = Invitation(
            tenant_id=tenant_b.id,
            email="invite_b@test.com",
            role="member",
            token="invite-b",
            expires_at=datetime.now(timezone.utc) + timedelta(days=1),
        )
        session.add_all([
            document_a,
            document_b,
            conversation_a,
            conversation_b,
            quota_a,
            quota_b,
            invitation_a,
            invitation_b,
        ])
        await session.flush()
        session.add_all([
            Message(
                tenant_id=tenant_a.id,
                conversation_id=conversation_a.id,
                role="assistant",
                content="Tenant A message",
            ),
            Message(
                tenant_id=tenant_b.id,
                conversation_id=conversation_b.id,
                role="assistant",
                content="Tenant B message",
            ),
        ])
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
        await session.execute(text("SELECT set_config('app.bypass_rls', 'off', false)"))
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
        await session.execute(text("SELECT set_config('app.bypass_rls', 'off', false)"))
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
        await session.execute(text("SELECT set_config('app.bypass_rls', 'off', false)"))
        result = await session.execute(select(User).order_by(User.email))
        users = result.scalars().all()

        assert len(users) == 0


@pytest.mark.asyncio
async def test_rls_bypass_with_set_tenant_id(setup_db):
    """Setting the tenant context allows seeing that tenant's rows."""
    async with SessionLocal() as session:
        await session.execute(text("SELECT set_config('app.bypass_rls', 'off', false)"))
        await session.execute(
            text(f"SET LOCAL app.current_tenant_id = '{setup_db['tenant_a_id']}'")
        )
        result = await session.execute(select(User))
        users_a = result.scalars().all()
        tenant_a_emails = [u.email for u in users_a]

    async with SessionLocal() as session:
        await session.execute(text("SELECT set_config('app.bypass_rls', 'off', false)"))
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
        await session.execute(text("SELECT set_config('app.bypass_rls', 'off', false)"))
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
        await session.execute(text("SELECT set_config('app.bypass_rls', 'off', false)"))
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
        await session.execute(text("SELECT set_config('app.bypass_rls', 'off', false)"))
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
        await session.execute(text("SELECT set_config('app.bypass_rls', 'off', false)"))
        await session.execute(
            text(f"SET LOCAL app.current_tenant_id = '{setup_db['tenant_a_id']}'")
        )
        result = await session.execute(
            select(User).where(User.email == "user_a@test.com")
        )
        user = result.scalar_one()
        assert user.full_name == "Updated User A"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("model", "tenant_a_attr", "tenant_b_attr"),
    [
        (Assistant, "Assistant A", "Assistant B"),
        (Document, "a.txt", "b.txt"),
        (Conversation, "session-a", "session-b"),
        (Message, "Tenant A message", "Tenant B message"),
        (QuotaLog, 1, 2),
        (Invitation, "invite_a@test.com", "invite_b@test.com"),
    ],
)
async def test_rls_isolation_all_tenant_tables(setup_db, model, tenant_a_attr, tenant_b_attr):
    """Every tenant table should hide rows from other tenants."""
    async with SessionLocal() as session:
        await session.execute(
            text(f"SET LOCAL app.current_tenant_id = '{setup_db['tenant_a_id']}'")
        )
        result = await session.execute(select(model))
        rows = result.scalars().all()

    assert len(rows) == 1
    row = rows[0]
    observed = (
        getattr(row, "name", None)
        or getattr(row, "filename", None)
        or getattr(row, "session_token", None)
        or getattr(row, "content", None)
        or getattr(row, "amount", None)
        or getattr(row, "email", None)
    )
    assert observed == tenant_a_attr
    assert observed != tenant_b_attr
