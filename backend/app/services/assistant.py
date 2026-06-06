import uuid
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from fastapi import HTTPException, status

from app.models.assistant import Assistant
from app.models.document import Document
from app.models.conversation import Conversation
from app.models.tenant import Tenant
from app.schemas.assistant import AssistantCreate, AssistantUpdate
from app.core.quotas import get_tenant_quotas
from app.services.storage import storage_service
from app.services.rag.chroma_client import chroma_client
from app.db.session import set_tenant_context

async def list_assistants(db: AsyncSession, tenant_id: uuid.UUID) -> list[Assistant]:
    """
    List all assistants for a given tenant.
    """
    result = await db.execute(
        select(Assistant).where(Assistant.tenant_id == tenant_id)
    )
    return list(result.scalars().all())

async def create_assistant(
    db: AsyncSession, tenant_id: uuid.UUID, payload: AssistantCreate
) -> Assistant:
    """
    Create a new assistant after checking the tenant's plan quota.
    """
    # 1. Fetch tenant to determine their plan
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )

    # 2. Check plan quotas
    quota = get_tenant_quotas(tenant.plan)
    if quota.max_assistants is not None:
        count_res = await db.execute(
            select(func.count(Assistant.id)).where(Assistant.tenant_id == tenant_id)
        )
        current_count = count_res.scalar_one()
        if current_count >= quota.max_assistants:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Limit of {quota.max_assistants} assistants exceeded for your plan."
            )

    # 3. Create assistant
    assistant = Assistant(
        tenant_id=tenant_id,
        name=payload.name,
        system_prompt=payload.system_prompt,
        model=payload.model,
        temperature=payload.temperature,
        max_tokens=payload.max_tokens,
        is_active=True,
        widget_config={}
    )
    db.add(assistant)
    await db.commit()
    await set_tenant_context(db, str(tenant_id))
    await db.refresh(assistant)
    return assistant

async def get_assistant(
    db: AsyncSession, tenant_id: uuid.UUID, assistant_id: uuid.UUID
) -> Assistant:
    """
    Fetch a single assistant by ID, ensuring it belongs to the tenant.
    """
    result = await db.execute(
        select(Assistant).where(
            Assistant.id == assistant_id,
            Assistant.tenant_id == tenant_id
        )
    )
    assistant = result.scalar_one_or_none()
    if not assistant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assistant not found"
        )
    return assistant

async def update_assistant(
    db: AsyncSession, tenant_id: uuid.UUID, assistant_id: uuid.UUID, payload: AssistantUpdate
) -> Assistant:
    """
    Update assistant settings.
    """
    assistant = await get_assistant(db, tenant_id, assistant_id)
    
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(assistant, field, value)

    await db.commit()
    await set_tenant_context(db, str(tenant_id))
    await db.refresh(assistant)
    return assistant

async def delete_assistant(
    db: AsyncSession, tenant_id: uuid.UUID, assistant_id: uuid.UUID
) -> None:
    """
    Delete an assistant.
    Blocks deletion if there are active conversations.
    Performs cascade deletion of database rows, MinIO storage objects, and ChromaDB vectors.
    """
    # 1. Fetch assistant and check existence
    assistant = await get_assistant(db, tenant_id, assistant_id)

    # 2. Check for active conversations
    conv_count_res = await db.execute(
        select(func.count(Conversation.id)).where(
            Conversation.assistant_id == assistant_id,
            Conversation.status == "active",
            Conversation.tenant_id == tenant_id
        )
    )
    active_conv_count = conv_count_res.scalar_one()
    if active_conv_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"This assistant has {active_conv_count} active conversations. Resolve or end them before deleting."
        )

    # 3. Retrieve all associated documents
    docs_res = await db.execute(
        select(Document).where(
            Document.assistant_id == assistant_id,
            Document.tenant_id == tenant_id
        )
    )
    documents = docs_res.scalars().all()

    cleanup_errors: list[str] = []

    # 4. Delete MinIO objects and ChromaDB vectors for each document
    for doc in documents:
        # Delete file from MinIO (run in threadpool since storage_service is synchronous)
        try:
            await asyncio.to_thread(storage_service.delete_file, doc.storage_key)
        except Exception as exc:
            cleanup_errors.append(
                f"MinIO cleanup failed for document {doc.id}: {exc}"
            )

        # Delete vectors from ChromaDB (run in threadpool since chromadb client is synchronous)
        try:
            await asyncio.to_thread(
                chroma_client.delete_document_vectors,
                str(tenant_id),
                str(doc.id)
            )
        except Exception as exc:
            cleanup_errors.append(
                f"ChromaDB cleanup failed for document {doc.id}: {exc}"
            )

    if cleanup_errors:
        # Keep the assistant in place so operators can retry cleanup instead of
        # leaving orphaned storage or vector data behind.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Assistant deletion aborted because associated storage cleanup failed.",
        )

    # 5. Delete assistant from database (cascade deletes will handle PostgreSQL rows)
    await db.delete(assistant)
    await db.commit()
