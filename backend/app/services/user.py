import uuid
import re
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.tenant import Tenant
from app.models.user import User
from app.core.security import get_password_hash
from fastapi import HTTPException, status

def validate_tenant_slug(slug: str) -> bool:
    """Validate tenant slug format: alphanumeric, lowercase, max 63 characters, min 1 character."""
    if not slug or len(slug) > 63:
        return False
    return bool(re.match(r"^[a-z0-9]+$", slug))

async def get_tenant_by_slug(db: AsyncSession, slug: str) -> Tenant | None:
    result = await db.execute(select(Tenant).where(Tenant.slug == slug))
    return result.scalar_one_or_none()

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

async def register_tenant_with_owner(
    db: AsyncSession,
    tenant_slug: str,
    tenant_name: str,
    owner_email: str,
    owner_password: str,
    owner_full_name: str | None = None,
) -> tuple[Tenant, User]:
    # 1. Validate slug format
    if not validate_tenant_slug(tenant_slug):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant slug must be lowercase, alphanumeric, and between 1 and 63 characters."
        )

    # 2. Check if slug is unique
    existing_tenant = await get_tenant_by_slug(db, tenant_slug)
    if existing_tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tenant slug '{tenant_slug}' is already taken."
        )

    # 3. Check if owner email is globally unique
    existing_user = await get_user_by_email(db, owner_email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Email '{owner_email}' is already registered."
        )

    # 4. Create Tenant
    tenant = Tenant(
        slug=tenant_slug,
        name=tenant_name,
        plan="starter",
        is_active=True,
        settings={},
        monthly_quota=1000,
        used_quota=0
    )
    db.add(tenant)
    await db.flush()  # Generate tenant.id

    # 5. Create Owner User
    hashed_password = get_password_hash(owner_password)
    user = User(
        tenant_id=tenant.id,
        email=owner_email,
        hashed_password=hashed_password,
        full_name=owner_full_name,
        role="owner",
        is_active=True
    )
    db.add(user)
    
    await db.commit()
    await db.refresh(tenant)
    await db.refresh(user)
    
    return tenant, user
