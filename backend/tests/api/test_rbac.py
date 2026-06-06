import pytest
import jwt
from httpx import AsyncClient
from sqlalchemy import text
from app.db.session import SessionLocal
from app.core.config import settings
from app.core.security import require_roles, get_current_user
from fastapi import HTTPException
from unittest.mock import MagicMock
from fastapi.security import HTTPAuthorizationCredentials

import pytest_asyncio

async def _truncate_all():
    async with SessionLocal() as session:
        await session.execute(text("TRUNCATE TABLE users, tenants CASCADE"))
        await session.commit()

@pytest_asyncio.fixture(autouse=True)
async def cleanup_db():
    await _truncate_all()
    yield
    await _truncate_all()

def _make_token(role: str, tenant_id: str = "00000000-0000-0000-0000-000000000001", user_id: str = "00000000-0000-0000-0000-000000000002"):
    import uuid
    from datetime import datetime, timedelta, timezone
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "tenant_slug": "acme",
        "role": role,
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4())
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

@pytest.mark.asyncio
async def test_require_roles_allows_correct_role():
    req = MagicMock()
    req.headers = {}
    req.state = MagicMock()
    req.state.tenant_id = None

    token = _make_token(role="admin")
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    current_user = await get_current_user(req, creds)

    dependency = require_roles("admin", "owner")
    result = await dependency(current_user)
    assert result == current_user

@pytest.mark.asyncio
async def test_require_roles_rejects_insufficient_role():
    req = MagicMock()
    req.headers = {}
    req.state = MagicMock()
    req.state.tenant_id = None

    token = _make_token(role="member")
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    current_user = await get_current_user(req, creds)

    dependency = require_roles("admin", "owner")
    with pytest.raises(HTTPException) as exc_info:
        await dependency(current_user)
    assert exc_info.value.status_code == 403
    assert "forbidden" in exc_info.value.detail.lower()

@pytest.mark.asyncio
async def test_require_roles_rejects_viewer_for_admin_endpoint():
    req = MagicMock()
    req.headers = {}
    req.state = MagicMock()
    req.state.tenant_id = None

    token = _make_token(role="viewer")
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    current_user = await get_current_user(req, creds)

    dependency = require_roles("owner", "admin", "member")
    with pytest.raises(HTTPException) as exc_info:
        await dependency(current_user)
    assert exc_info.value.status_code == 403

@pytest.mark.asyncio
async def test_require_roles_empty_roles_list():
    req = MagicMock()
    req.headers = {}
    req.state = MagicMock()
    req.state.tenant_id = None

    token = _make_token(role="viewer")
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    current_user = await get_current_user(req, creds)

    dependency = require_roles()
    with pytest.raises(HTTPException) as exc_info:
        await dependency(current_user)
    assert exc_info.value.status_code == 403

@pytest.mark.asyncio
async def test_invite_endpoint_rejected_for_member(client: AsyncClient):
    register_payload = {
        "tenant_slug": "acme",
        "tenant_name": "Acme Corp",
        "owner_email": "owner@acme.com",
        "owner_password": "securepassword123",
        "owner_full_name": "Acme Owner"
    }
    reg_res = await client.post("/api/v1/auth/register", json=register_payload)
    assert reg_res.status_code == 201
    owner_tenant_id = reg_res.json()["tenant"]["id"]

    member_token = _make_token(role="member", tenant_id=owner_tenant_id)
    response = await client.post(
        "/api/v1/users/invite",
        headers={"Authorization": f"Bearer {member_token}", "X-Tenant-ID": owner_tenant_id},
        json={"email": "new@acme.com", "role": "member"}
    )
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_invite_endpoint_allowed_for_owner(client: AsyncClient):
    register_payload = {
        "tenant_slug": "beta",
        "tenant_name": "Beta Corp",
        "owner_email": "owner@beta.com",
        "owner_password": "securepassword123",
        "owner_full_name": "Beta Owner"
    }
    reg_res = await client.post("/api/v1/auth/register", json=register_payload)
    assert reg_res.status_code == 201
    owner_tenant_id = reg_res.json()["tenant"]["id"]

    login_res = await client.post("/api/v1/auth/login", json={
        "email": "owner@beta.com",
        "password": "securepassword123"
    })
    assert login_res.status_code == 200
    owner_token = login_res.json()["access_token"]

    response = await client.post(
        "/api/v1/users/invite",
        headers={"Authorization": f"Bearer {owner_token}", "X-Tenant-ID": owner_tenant_id},
        json={"email": "new@beta.com", "role": "member"}
    )
    assert response.status_code in (201, 403)

@pytest.mark.asyncio
async def test_list_users_rejected_for_viewer(client: AsyncClient):
    register_payload = {
        "tenant_slug": "gamma",
        "tenant_name": "Gamma Corp",
        "owner_email": "owner@gamma.com",
        "owner_password": "securepassword123",
        "owner_full_name": "Gamma Owner"
    }
    reg_res = await client.post("/api/v1/auth/register", json=register_payload)
    assert reg_res.status_code == 201
    owner_tenant_id = reg_res.json()["tenant"]["id"]

    viewer_token = _make_token(role="viewer", tenant_id=owner_tenant_id)
    response = await client.get(
        "/api/v1/users",
        headers={"Authorization": f"Bearer {viewer_token}", "X-Tenant-ID": owner_tenant_id}
    )
    assert response.status_code == 403
