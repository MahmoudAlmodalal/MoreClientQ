import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.core.security import require_roles
from app.models.user import User
from app.models.tenant import Tenant
from app.models.invitation import Invitation
from app.schemas.team import (
    InviteRequest,
    InviteResponseWrapper,
    InviteResponse,
    UserListResponse,
    UpdateRoleRequest,
    UpdateRoleResponse,
    UpdateRoleData,
    DeleteUserResponse,
)
from app.services.auth import create_invitation

router = APIRouter()


def _get_tenant_id_from_user(current_user: dict) -> str:
    return current_user.get("tenant_id", "")


@router.get("", response_model=list[UserListResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("owner", "admin", "member")),
):
    tenant_id = _get_tenant_id_from_user(current_user)
    result = await db.execute(
        select(User).where(User.tenant_id == uuid.UUID(tenant_id))
    )
    users = result.scalars().all()
    return users


@router.post("/invite", response_model=InviteResponseWrapper, status_code=status.HTTP_201_CREATED)
async def invite_user(
    payload: InviteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("owner", "admin")),
):
    tenant_id = uuid.UUID(_get_tenant_id_from_user(current_user))
    invitation = await create_invitation(
        db=db,
        tenant_id=tenant_id,
        email=payload.email,
        role=payload.role,
    )

    # Fetch tenant for slug
    tenant = await db.get(Tenant, tenant_id)
    tenant_slug = tenant.slug if tenant else "unknown"
    invitation_link = f"http://{tenant_slug}.localhost:3000/register?token={invitation.token}"

    return InviteResponseWrapper(
        data=InviteResponse(
            id=invitation.id,
            email=invitation.email,
            role=invitation.role,
            invitation_link=invitation_link,
        )
    )


@router.patch("/{user_id}", response_model=UpdateRoleResponse)
async def update_user_role(
    user_id: str,
    payload: UpdateRoleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("owner", "admin")),
):
    current_tenant_id = _get_tenant_id_from_user(current_user)
    current_role = current_user.get("role", "")

    user_uuid = uuid.UUID(user_id) if user_id else None
    result = await db.execute(
        select(User).where(User.id == user_uuid, User.tenant_id == uuid.UUID(current_tenant_id))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Prevent non-owner from changing an owner's role
    if user.role == "owner" and current_role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can change the role of another owner"
        )

    # Prevent changing the last owner
    if user.role == "owner" and payload.role != "owner":
        owner_count = await db.execute(
            select(User).where(
                User.tenant_id == uuid.UUID(current_tenant_id),
                User.role == "owner"
            )
        )
        if len(owner_count.scalars().all()) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change the role of the last owner"
            )

    user.role = payload.role
    await db.commit()
    await db.refresh(user)

    return UpdateRoleResponse(
        data=UpdateRoleData(id=user.id, role=user.role)
    )


@router.delete("/{user_id}", response_model=DeleteUserResponse)
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("owner", "admin")),
):
    current_tenant_id = _get_tenant_id_from_user(current_user)
    current_user_id = current_user.get("sub", "")

    user_uuid = uuid.UUID(user_id) if user_id else None
    result = await db.execute(
        select(User).where(User.id == user_uuid, User.tenant_id == uuid.UUID(current_tenant_id))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Prevent self-deletion
    if str(user.id) == current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot delete yourself"
        )

    # Prevent deleting the last owner
    if user.role == "owner":
        owner_count = await db.execute(
            select(User).where(
                User.tenant_id == uuid.UUID(current_tenant_id),
                User.role == "owner"
            )
        )
        if len(owner_count.scalars().all()) <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the last owner of the tenant"
            )

    await db.delete(user)
    await db.commit()

    return DeleteUserResponse()
