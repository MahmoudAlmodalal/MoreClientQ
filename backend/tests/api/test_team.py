import pytest
import jwt
from httpx import AsyncClient
from sqlalchemy import text
from app.db.session import SessionLocal, enable_rls_bypass
from app.core.config import settings
from app.models.invitation import Invitation
from app.models.user import User
from app.models.tenant import Tenant
from app.core.redis import redis_cache

import pytest_asyncio

async def _truncate_all():
    async with SessionLocal() as session:
        await enable_rls_bypass(session)
        await session.execute(text("TRUNCATE TABLE users, tenants, invitations CASCADE"))
        await session.commit()

@pytest_asyncio.fixture(autouse=True)
async def cleanup_db():
    await _truncate_all()
    yield
    await _truncate_all()

@pytest_asyncio.fixture
async def registered_owner(client: AsyncClient):
    payload = {
        "tenant_slug": "acme",
        "tenant_name": "Acme Corp",
        "owner_email": "owner@acme.com",
        "owner_password": "securepassword123",
        "owner_full_name": "Acme Owner"
    }
    reg_res = await client.post("/api/v1/auth/register", json=payload)
    assert reg_res.status_code == 201
    tenant_id = reg_res.json()["tenant"]["id"]
    login_res = await client.post("/api/v1/auth/login", json={
        "email": "owner@acme.com",
        "password": "securepassword123"
    })
    assert login_res.status_code == 200
    return {
        "tenant_id": tenant_id,
        "access_token": login_res.json()["access_token"],
        "tenant_slug": "acme"
    }


@pytest.mark.asyncio
async def test_invite_creation(client: AsyncClient, registered_owner):
    response = await client.post(
        "/api/v1/users/invite",
        headers={
            "Authorization": f"Bearer {registered_owner['access_token']}",
            "X-Tenant-ID": registered_owner["tenant_id"]
        },
        json={"email": "member@acme.com", "role": "member"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["email"] == "member@acme.com"
    assert data["data"]["role"] == "member"
    assert "invitation_link" in data["data"]
    assert data["data"]["invitation_link"].startswith("http")

    # Verify invitation record in database
    async with SessionLocal() as session:
        await enable_rls_bypass(session)
        from sqlalchemy import select
        result = await session.execute(
            select(Invitation).where(Invitation.email == "member@acme.com")
        )
        inv = result.scalar_one_or_none()
        assert inv is not None
        assert inv.role == "member"
        assert inv.accepted_at is None
        assert inv.token is not None


@pytest.mark.asyncio
async def test_invite_duplicate_email_rejected(client: AsyncClient, registered_owner):
    # First invite
    await client.post(
        "/api/v1/users/invite",
        headers={
            "Authorization": f"Bearer {registered_owner['access_token']}",
            "X-Tenant-ID": registered_owner["tenant_id"]
        },
        json={"email": "member@acme.com", "role": "member"}
    )
    # Duplicate invite
    response = await client.post(
        "/api/v1/users/invite",
        headers={
            "Authorization": f"Bearer {registered_owner['access_token']}",
            "X-Tenant-ID": registered_owner["tenant_id"]
        },
        json={"email": "member@acme.com", "role": "member"}
    )
    assert response.status_code == 409
    assert "already invited" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_invite_member_rejected(client: AsyncClient, registered_owner):
    # Create a member token manually
    import uuid
    from datetime import datetime, timedelta, timezone
    member_token = jwt.encode({
        "sub": str(uuid.uuid4()),
        "tenant_id": registered_owner["tenant_id"],
        "tenant_slug": "acme",
        "role": "member",
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4())
    }, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    response = await client.post(
        "/api/v1/users/invite",
        headers={
            "Authorization": f"Bearer {member_token}",
            "X-Tenant-ID": registered_owner["tenant_id"]
        },
        json={"email": "new@acme.com", "role": "member"}
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_accept_invitation(client: AsyncClient, registered_owner):
    # Create an invitation first
    invite_res = await client.post(
        "/api/v1/users/invite",
        headers={
            "Authorization": f"Bearer {registered_owner['access_token']}",
            "X-Tenant-ID": registered_owner["tenant_id"]
        },
        json={"email": "member@acme.com", "role": "member"}
    )
    assert invite_res.status_code == 201
    invite_token = invite_res.json()["data"]["invitation_link"].split("token=")[1]

    # Accept the invitation
    accept_res = await client.post(
        "/api/v1/auth/invite/accept",
        json={"token": invite_token, "password": "newpassword123"}
    )
    assert accept_res.status_code == 200
    data = accept_res.json()
    assert data["status"] == "success"
    assert data["data"]["email"] == "member@acme.com"
    assert data["data"]["role"] == "member"

    # Verify user was created
    async with SessionLocal() as session:
        await enable_rls_bypass(session)
        from sqlalchemy import select
        user_res = await session.execute(
            select(User).where(User.email == "member@acme.com")
        )
        user = user_res.scalar_one_or_none()
        assert user is not None
        assert user.role == "member"
        assert user.is_active
        assert user.hashed_password is not None

        # Verify invitation marked as accepted
        inv_res = await session.execute(
            select(Invitation).where(Invitation.token == invite_token)
        )
        inv = inv_res.scalar_one_or_none()
        assert inv is not None
        assert inv.accepted_at is not None


@pytest.mark.asyncio
async def test_accept_invitation_invalid_token(client: AsyncClient, registered_owner):
    response = await client.post(
        "/api/v1/auth/invite/accept",
        json={"token": "invalid-token", "password": "newpassword123"}
    )
    assert response.status_code == 404
    assert "invalid" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_accept_invitation_expired_token(client: AsyncClient, registered_owner):
    # Manually create an expired invitation
    import uuid
    from datetime import datetime, timedelta, timezone
    async with SessionLocal() as session:
        await enable_rls_bypass(session)
        inv = Invitation(
            tenant_id=uuid.UUID(registered_owner["tenant_id"]),
            email="expired@acme.com",
            role="member",
            token="expired-token-123",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        session.add(inv)
        await session.commit()

    response = await client.post(
        "/api/v1/auth/invite/accept",
        json={"token": "expired-token-123", "password": "newpassword123"}
    )
    assert response.status_code == 410
    assert "expired" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_list_users(client: AsyncClient, registered_owner):
    response = await client.get(
        "/api/v1/users",
        headers={
            "Authorization": f"Bearer {registered_owner['access_token']}",
            "X-Tenant-ID": registered_owner["tenant_id"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    emails = [u["email"] for u in data]
    assert "owner@acme.com" in emails


@pytest.mark.asyncio
async def test_update_user_role(client: AsyncClient, registered_owner):
    # Create a member via invitation
    invite_res = await client.post(
        "/api/v1/users/invite",
        headers={
            "Authorization": f"Bearer {registered_owner['access_token']}",
            "X-Tenant-ID": registered_owner["tenant_id"]
        },
        json={"email": "member@acme.com", "role": "member"}
    )
    assert invite_res.status_code == 201
    invite_token = invite_res.json()["data"]["invitation_link"].split("token=")[1]

    await client.post(
        "/api/v1/auth/invite/accept",
        json={"token": invite_token, "password": "newpassword123"}
    )

    # Get the member's user ID
    list_res = await client.get(
        "/api/v1/users",
        headers={
            "Authorization": f"Bearer {registered_owner['access_token']}",
            "X-Tenant-ID": registered_owner["tenant_id"]
        }
    )
    users = list_res.json()
    member = [u for u in users if u["email"] == "member@acme.com"][0]
    member_id = member["id"]

    # Update role
    update_res = await client.patch(
        f"/api/v1/users/{member_id}",
        headers={
            "Authorization": f"Bearer {registered_owner['access_token']}",
            "X-Tenant-ID": registered_owner["tenant_id"]
        },
        json={"role": "admin"}
    )
    assert update_res.status_code == 200
    assert update_res.json()["data"]["role"] == "admin"


@pytest.mark.asyncio
async def test_delete_user(client: AsyncClient, registered_owner):
    # Create a member via invitation
    invite_res = await client.post(
        "/api/v1/users/invite",
        headers={
            "Authorization": f"Bearer {registered_owner['access_token']}",
            "X-Tenant-ID": registered_owner["tenant_id"]
        },
        json={"email": "member@acme.com", "role": "member"}
    )
    assert invite_res.status_code == 201
    invite_token = invite_res.json()["data"]["invitation_link"].split("token=")[1]

    await client.post(
        "/api/v1/auth/invite/accept",
        json={"token": invite_token, "password": "newpassword123"}
    )

    list_res = await client.get(
        "/api/v1/users",
        headers={
            "Authorization": f"Bearer {registered_owner['access_token']}",
            "X-Tenant-ID": registered_owner["tenant_id"]
        }
    )
    users = list_res.json()
    member = [u for u in users if u["email"] == "member@acme.com"][0]
    member_id = member["id"]

    # Delete user
    delete_res = await client.delete(
        f"/api/v1/users/{member_id}",
        headers={
            "Authorization": f"Bearer {registered_owner['access_token']}",
            "X-Tenant-ID": registered_owner["tenant_id"]
        }
    )
    assert delete_res.status_code == 200
    assert delete_res.json()["status"] == "success"

    # Verify user removed
    list_res2 = await client.get(
        "/api/v1/users",
        headers={
            "Authorization": f"Bearer {registered_owner['access_token']}",
            "X-Tenant-ID": registered_owner["tenant_id"]
        }
    )
    emails = [u["email"] for u in list_res2.json()]
    assert "member@acme.com" not in emails


@pytest.mark.asyncio
async def test_owner_cannot_delete_self(client: AsyncClient, registered_owner):
    list_res = await client.get(
        "/api/v1/users",
        headers={
            "Authorization": f"Bearer {registered_owner['access_token']}",
            "X-Tenant-ID": registered_owner["tenant_id"]
        }
    )
    users = list_res.json()
    owner = [u for u in users if u["email"] == "owner@acme.com"][0]
    owner_id = owner["id"]

    delete_res = await client.delete(
        f"/api/v1/users/{owner_id}",
        headers={
            "Authorization": f"Bearer {registered_owner['access_token']}",
            "X-Tenant-ID": registered_owner["tenant_id"]
        }
    )
    assert delete_res.status_code == 403


@pytest.mark.asyncio
async def test_tenant_offboarding(client: AsyncClient, registered_owner):
    # Create a member first
    invite_res = await client.post(
        "/api/v1/users/invite",
        headers={
            "Authorization": f"Bearer {registered_owner['access_token']}",
            "X-Tenant-ID": registered_owner["tenant_id"]
        },
        json={"email": "member@acme.com", "role": "member"}
    )
    assert invite_res.status_code == 201
    invite_token = invite_res.json()["data"]["invitation_link"].split("token=")[1]
    await client.post(
        "/api/v1/auth/invite/accept",
        json={"token": invite_token, "password": "newpassword123"}
    )

    # Offboard the tenant
    offboard_res = await client.delete(
        "/api/v1/tenants/self",
        headers={
            "Authorization": f"Bearer {registered_owner['access_token']}",
            "X-Tenant-ID": registered_owner["tenant_id"]
        }
    )
    assert offboard_res.status_code == 200
    assert offboard_res.json()["status"] == "success"

    # Verify tenant no longer exists
    async with SessionLocal() as session:
        await enable_rls_bypass(session)
        from sqlalchemy import select
        tenant_res = await session.execute(
            select(Tenant).where(Tenant.slug == "acme")
        )
        assert tenant_res.scalar_one_or_none() is None

        # Verify users cascade deleted
        user_res = await session.execute(
            select(User).where(User.email == "member@acme.com")
        )
        assert user_res.scalar_one_or_none() is None

        # Verify invitations cascade deleted
        inv_res = await session.execute(
            select(Invitation).where(Invitation.email == "member@acme.com")
        )
        assert inv_res.scalar_one_or_none() is None

    token_after_offboard = await client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {registered_owner['access_token']}",
            "X-Tenant-ID": registered_owner["tenant_id"],
        }
    )
    assert token_after_offboard.status_code == 403
    assert await redis_cache.exists(f"tenant:revoked:{registered_owner['tenant_id']}")
