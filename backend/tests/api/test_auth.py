import pytest
import uuid
import jwt
from httpx import AsyncClient
from sqlalchemy import select, delete, update
from app.db.session import SessionLocal
from app.models.tenant import Tenant
from app.models.user import User
from app.core.config import settings
from app.core.security import get_current_user, verify_token
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

import pytest_asyncio

@pytest_asyncio.fixture(autouse=True)
async def cleanup_db():
    # Run before test
    async with SessionLocal() as session:
        await session.execute(delete(User))
        await session.execute(delete(Tenant))
        await session.commit()
    yield
    # Run after test
    async with SessionLocal() as session:
        await session.execute(delete(User))
        await session.execute(delete(Tenant))
        await session.commit()

@pytest_asyncio.fixture
async def registered_user(client: AsyncClient):

    payload = {
        "tenant_slug": "acme",
        "tenant_name": "Acme Corp",
        "owner_email": "owner@acme.com",
        "owner_password": "securepassword123",
        "owner_full_name": "Acme Owner"
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    return payload

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, registered_user):
    payload = {
        "email": registered_user["owner_email"],
        "password": registered_user["owner_password"]
    }
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    # Decode access token and verify claims
    claims = jwt.decode(
        data["access_token"],
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM]
    )
    assert "sub" in claims
    assert "tenant_id" in claims
    assert claims["tenant_slug"] == "acme"
    assert claims["role"] == "owner"
    assert claims["type"] == "access"

    # Decode refresh token and verify claims
    refresh_claims = jwt.decode(
        data["refresh_token"],
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM]
    )
    assert refresh_claims["sub"] == claims["sub"]
    assert refresh_claims["tenant_id"] == claims["tenant_id"]
    assert refresh_claims["tenant_slug"] == "acme"
    assert refresh_claims["role"] == "owner"
    assert refresh_claims["type"] == "refresh"

@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient, registered_user):
    # Wrong password
    payload = {
        "email": registered_user["owner_email"],
        "password": "wrongpassword"
    }
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"

    # Wrong email
    payload = {
        "email": "wrong@acme.com",
        "password": registered_user["owner_password"]
    }
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"

@pytest.mark.asyncio
async def test_login_deactivated_account(client: AsyncClient, registered_user):
    # Deactivate the user in DB
    async with SessionLocal() as session:
        await session.execute(
            update(User)
            .where(User.email == registered_user["owner_email"])
            .values(is_active=False)
        )
        await session.commit()

    payload = {
        "email": registered_user["owner_email"],
        "password": registered_user["owner_password"]
    }
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 403
    assert "deactivated" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_login_deactivated_tenant(client: AsyncClient, registered_user):
    # Deactivate the tenant in DB
    async with SessionLocal() as session:
        await session.execute(
            update(Tenant)
            .where(Tenant.slug == "acme")
            .values(is_active=False)
        )
        await session.commit()

    payload = {
        "email": registered_user["owner_email"],
        "password": registered_user["owner_password"]
    }
    response = await client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 403
    assert "tenant deactivated" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_token_refresh_success(client: AsyncClient, registered_user):
    # First login to get refresh token
    login_payload = {
        "email": registered_user["owner_email"],
        "password": registered_user["owner_password"]
    }
    login_res = await client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    refresh_token = login_res.json()["refresh_token"]

    # Call refresh endpoint
    refresh_payload = {
        "refresh_token": refresh_token
    }
    response = await client.post("/api/v1/auth/refresh", json=refresh_payload)
    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    # Verify new access token is valid
    claims = jwt.decode(
        data["access_token"],
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM]
    )
    assert claims["tenant_slug"] == "acme"
    assert claims["role"] == "owner"
    assert claims["type"] == "access"

@pytest.mark.asyncio
async def test_token_refresh_invalid_or_expired(client: AsyncClient, registered_user):
    # Invalid token string
    refresh_payload = {
        "refresh_token": "not-a-valid-jwt-token"
    }
    response = await client.post("/api/v1/auth/refresh", json=refresh_payload)
    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()

    # Access token used as refresh token
    login_payload = {
        "email": registered_user["owner_email"],
        "password": registered_user["owner_password"]
    }
    login_res = await client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    access_token = login_res.json()["access_token"]

    refresh_payload = {
        "refresh_token": access_token
    }
    response = await client.post("/api/v1/auth/refresh", json=refresh_payload)
    assert response.status_code == 401
    assert "invalid" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_dependency_get_current_user():
    # Mock FastAPI request and credentials
    from unittest.mock import MagicMock
    request = MagicMock(spec=Request)
    request.headers = {}
    request.state = MagicMock()
    request.state.tenant_id = None

    # Test not authenticated (no credentials)
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(request, credentials=None)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Not authenticated"

    # Test invalid token
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="invalid-token")
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(request, credentials=credentials)
    assert exc_info.value.status_code == 401
    assert "invalid" in exc_info.value.detail.lower()
