from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
import uuid

from app.db.session import get_db
from app.schemas.auth import (
    TenantRegister,
    RegistrationResponse,
    LoginRequest,
    TokenResponse,
    TokenRefreshRequest
)
from app.services.user import register_tenant_with_owner, get_user_by_email
from app.models.tenant import Tenant
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token
)
from app.core.config import settings

router = APIRouter()

@router.post("/register", response_model=RegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: TenantRegister,
    db: AsyncSession = Depends(get_db)
):
    """Register a new tenant and its primary owner account."""
    tenant, owner = await register_tenant_with_owner(
        db=db,
        tenant_slug=payload.tenant_slug,
        tenant_name=payload.tenant_name,
        owner_email=payload.owner_email,
        owner_password=payload.owner_password,
        owner_full_name=payload.owner_full_name
    )
    return {"tenant": tenant, "owner": owner}

@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate credentials and return session tokens."""
    user = await get_user_by_email(db, payload.email)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account deactivated"
        )

    # Fetch tenant
    tenant = await db.get(Tenant, user.tenant_id)
    if not tenant or not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant deactivated or not found"
        )

    # Generate tokens
    access_token = create_access_token(
        subject=str(user.id),
        tenant_id=str(user.tenant_id),
        tenant_slug=tenant.slug,
        role=user.role
    )
    refresh_token = create_refresh_token(
        subject=str(user.id),
        tenant_id=str(user.tenant_id),
        tenant_slug=tenant.slug,
        role=user.role
    )

    # Update last login
    user.last_login = datetime.now(timezone.utc)
    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db)
):
    """Generate a new access token using a refresh token."""
    token_claims = verify_token(payload.refresh_token)
    if not token_claims or token_claims.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    user_id = token_claims.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    # Fetch user
    from app.models.user import User
    user = await db.get(User, uuid.UUID(user_id))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    # Fetch tenant
    tenant = await db.get(Tenant, user.tenant_id)
    if not tenant or not tenant.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant deactivated"
        )

    # Generate a new access token
    access_token = create_access_token(
        subject=str(user.id),
        tenant_id=str(user.tenant_id),
        tenant_slug=tenant.slug,
        role=user.role
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

