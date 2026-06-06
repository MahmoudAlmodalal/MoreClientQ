import pytest
from httpx import AsyncClient
from sqlalchemy import select, text
from app.db.session import SessionLocal
from app.db.session import enable_rls_bypass
from app.models.tenant import Tenant
from app.models.user import User

import pytest_asyncio

async def _truncate_all():
    """Truncate all tenant-related tables bypassing RLS."""
    async with SessionLocal() as session:
        # TRUNCATE bypasses RLS entirely
        await session.execute(text("TRUNCATE TABLE users, tenants CASCADE"))
        await session.commit()

@pytest_asyncio.fixture(autouse=True)
async def cleanup_db():
    await _truncate_all()
    yield
    await _truncate_all()




@pytest.mark.asyncio
async def test_registration_success(client: AsyncClient):
    payload = {
        "tenant_slug": "acme",
        "tenant_name": "Acme Corp",
        "owner_email": "owner@acme.com",
        "owner_password": "securepassword123",
        "owner_full_name": "Acme Owner"
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    
    data = response.json()
    assert "tenant" in data
    assert "owner" in data
    assert data["tenant"]["slug"] == "acme"
    assert data["tenant"]["name"] == "Acme Corp"
    assert data["owner"]["email"] == "owner@acme.com"
    assert data["owner"]["role"] == "owner"
    assert "id" in data["tenant"]
    assert "id" in data["owner"]
    assert "hashed_password" not in data["owner"]

    # Verify db records exist
    async with SessionLocal() as session:
        await enable_rls_bypass(session)
        # Check Tenant
        tenant_res = await session.execute(select(Tenant).where(Tenant.slug == "acme"))
        tenant = tenant_res.scalar_one_or_none()
        assert tenant is not None
        assert tenant.name == "Acme Corp"
        
        # Check User
        user_res = await session.execute(select(User).where(User.email == "owner@acme.com"))
        user = user_res.scalar_one_or_none()
        assert user is not None
        assert user.tenant_id == tenant.id
        assert user.role == "owner"

@pytest.mark.asyncio
async def test_registration_duplicate_slug(client: AsyncClient):
    payload = {
        "tenant_slug": "acme",
        "tenant_name": "Acme Corp",
        "owner_email": "owner@acme.com",
        "owner_password": "securepassword123",
        "owner_full_name": "Acme Owner"
    }
    # Register first tenant
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201

    # Register second tenant with same slug but different email
    payload_dup = payload.copy()
    payload_dup["owner_email"] = "other@acme.com"
    response_dup = await client.post("/api/v1/auth/register", json=payload_dup)
    assert response_dup.status_code == 400
    assert "slug" in response_dup.json()["detail"].lower()

@pytest.mark.asyncio
async def test_registration_global_email_uniqueness(client: AsyncClient):
    payload1 = {
        "tenant_slug": "acme",
        "tenant_name": "Acme Corp",
        "owner_email": "owner@shared.com",
        "owner_password": "securepassword123",
        "owner_full_name": "Acme Owner"
    }
    response1 = await client.post("/api/v1/auth/register", json=payload1)
    assert response1.status_code == 201

    payload2 = {
        "tenant_slug": "beta",
        "tenant_name": "Beta Corp",
        "owner_email": "owner@shared.com",
        "owner_password": "securepassword123",
        "owner_full_name": "Beta Owner"
    }
    response2 = await client.post("/api/v1/auth/register", json=payload2)
    assert response2.status_code == 400
    assert "email" in response2.json()["detail"].lower()

@pytest.mark.asyncio
@pytest.mark.parametrize("slug", [
    "ACME",       # Upper case
    "acme_corp",  # Contains underscore (wait, slug format: lowercase, alphanumeric, so no underscores?)
    "acme!",      # Contains special character
    "a" * 64,     # Too long
    "",           # Empty
])
async def test_registration_invalid_slug_format(client: AsyncClient, slug: str):
    payload = {
        "tenant_slug": slug,
        "tenant_name": "Test Corp",
        "owner_email": "owner@test.com",
        "owner_password": "securepassword123",
        "owner_full_name": "Test Owner"
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code in [400, 422]
