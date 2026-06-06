import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.config import settings
from app.core.security import require_roles
from app.schemas.assistant import AssistantCreate, AssistantUpdate, AssistantResponse
from app.services import assistant as assistant_service

router = APIRouter()

def _get_tenant_id_from_user(current_user: dict) -> uuid.UUID:
    tenant_id_str = current_user.get("tenant_id", "")
    if not tenant_id_str:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant ID not found in credentials"
        )
    return uuid.UUID(tenant_id_str)


@router.get("", response_model=list[AssistantResponse])
async def list_assistants(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("owner", "admin", "member")),
):
    """
    List all assistants for the tenant.
    """
    tenant_id = _get_tenant_id_from_user(current_user)
    return await assistant_service.list_assistants(db=db, tenant_id=tenant_id)


@router.post("", response_model=AssistantResponse, status_code=status.HTTP_201_CREATED)
async def create_assistant(
    payload: AssistantCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("owner", "admin")),
):
    """
    Create a new assistant. Restricted to owners and admins.
    """
    tenant_id = _get_tenant_id_from_user(current_user)
    return await assistant_service.create_assistant(db=db, tenant_id=tenant_id, payload=payload)


@router.get("/{id}", response_model=AssistantResponse)
async def get_assistant(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("owner", "admin", "member")),
):
    """
    Get assistant details.
    """
    tenant_id = _get_tenant_id_from_user(current_user)
    return await assistant_service.get_assistant(db=db, tenant_id=tenant_id, assistant_id=id)


@router.patch("/{id}", response_model=AssistantResponse)
async def update_assistant(
    id: uuid.UUID,
    payload: AssistantUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("owner", "admin")),
):
    """
    Update assistant configuration. Restricted to owners and admins.
    """
    tenant_id = _get_tenant_id_from_user(current_user)
    return await assistant_service.update_assistant(
        db=db, tenant_id=tenant_id, assistant_id=id, payload=payload
    )


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assistant(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("owner", "admin")),
):
    """
    Delete assistant. Restricted to owners and admins.
    """
    tenant_id = _get_tenant_id_from_user(current_user)
    await assistant_service.delete_assistant(db=db, tenant_id=tenant_id, assistant_id=id)


@router.get("/{id}/embed")
async def get_widget_embed_code(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("owner", "admin")),
):
    """
    Retrieve the widget embed code snippet for an assistant.
    """
    tenant_id = _get_tenant_id_from_user(current_user)
    # Validate assistant existence
    await assistant_service.get_assistant(db=db, tenant_id=tenant_id, assistant_id=id)
    
    widget_base_url = settings.WIDGET_BASE_URL.rstrip("/")
    snippet = (
        f'<script src="{widget_base_url}/widget.js" '
        f'data-assistant="{id}" '
        'data-theme="light" '
        'data-position="bottom-right"></script>'
    )
    return {"snippet": snippet}
