import uuid
import secrets
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.models.invitation import Invitation
from app.models.user import User
from app.models.tenant import Tenant
from app.db.session import set_tenant_context, enable_rls_bypass
from app.core.security import get_password_hash
from fastapi import HTTPException, status




def generate_invitation_token() -> str:
    """Generate a cryptographically secure invitation token."""
    return f"inv_tok_{secrets.token_urlsafe(32)}"


async def create_invitation(
    db: AsyncSession,
    tenant_id: uuid.UUID,
    email: str,
    role: str,
    invited_by_user_id: uuid.UUID | None = None,
) -> Invitation:
    # Check if user with this email already exists in this tenant
    existing_user = await db.execute(
        select(User).where(User.email == email, User.tenant_id == tenant_id)
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists in the tenant"
        )

    # Check if there's already a pending invitation for this email in this tenant
    existing_invitation = await db.execute(
        select(Invitation).where(
            Invitation.email == email,
            Invitation.tenant_id == tenant_id,
            Invitation.accepted_at.is_(None),
            Invitation.expires_at > datetime.now(timezone.utc)
        )
    )
    if existing_invitation.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already invited"
        )

    token = generate_invitation_token()
    invitation = Invitation(
        tenant_id=tenant_id,
        email=email,
        role=role,
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db.add(invitation)
    await db.commit()
    await set_tenant_context(db, str(tenant_id))
    await db.refresh(invitation)
    return invitation


async def accept_invitation(
    db: AsyncSession,
    token: str,
    password: str,
) -> tuple[User, str]:
    # Find the invitation by token
    await enable_rls_bypass(db)
    result = await db.execute(
        select(Invitation).where(Invitation.token == token)
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid invitation token"
        )

    if invitation.accepted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Invitation has already been accepted"
        )

    if invitation.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Invitation has expired"
        )

    # Check if user with this email already exists (global uniqueness)
    existing_user = await db.execute(
        select(User).where(User.email == invitation.email)
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists"
        )

    # Create the user
    hashed_password = get_password_hash(password)
    user = User(
        tenant_id=invitation.tenant_id,
        email=invitation.email,
        hashed_password=hashed_password,
        role=invitation.role,
        is_active=True,
    )
    db.add(user)

    # Mark invitation as accepted
    invitation.accepted_at = datetime.now(timezone.utc)
    await db.commit()
    await set_tenant_context(db, str(invitation.tenant_id))
    await db.refresh(user)

    return user, invitation.email
