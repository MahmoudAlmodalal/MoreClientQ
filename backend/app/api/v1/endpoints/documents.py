import uuid
import io
import httpx
import asyncio
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.db.session import get_db, set_tenant_context
from app.core.security import require_roles
from app.core.quotas import get_tenant_quotas, ALLOWED_DOCUMENT_FILE_TYPES, MAX_UPLOAD_SIZE_BYTES
from app.models.assistant import Assistant
from app.models.document import Document
from app.models.tenant import Tenant
from app.schemas.document import DocumentResponse, DocumentStatusResponse, URLIngestRequest
from app.services.storage import storage_service
from app.services.rag.chroma_client import chroma_client
from app.tasks.ingest import ingest_document
from app.tasks.celery_app import celery_app

router = APIRouter()

def _get_tenant_id_from_user(current_user: dict) -> uuid.UUID:
    tenant_id_str = current_user.get("tenant_id", "")
    if not tenant_id_str:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant ID not found in credentials"
        )
    return uuid.UUID(tenant_id_str)

async def _verify_assistant(db: AsyncSession, tenant_id: uuid.UUID, assistant_id: uuid.UUID) -> Assistant:
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

async def _check_document_quota(db: AsyncSession, tenant_id: uuid.UUID) -> None:
    tenant_res = await db.execute(
        select(Tenant).where(Tenant.id == tenant_id).with_for_update()
    )
    tenant = tenant_res.scalar_one_or_none()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    quota = get_tenant_quotas(tenant.plan)
    if quota.max_documents is not None:
        count_res = await db.execute(
            select(func.count(Document.id)).where(Document.tenant_id == tenant_id)
        )
        current_count = count_res.scalar_one()
        if current_count >= quota.max_documents:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Limit of {quota.max_documents} documents exceeded for your plan."
            )

@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    assistant_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("owner", "admin")),
):
    """
    Upload a document file to the assistant's knowledge base.
    Restricted to owners and admins.
    """
    # 1. Validate file extension/suffix
    filename = file.filename or "uploaded_file"
    suffix = filename.split(".")[-1].lower() if "." in filename else ""
    if suffix not in ALLOWED_DOCUMENT_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Allowed: PDF, DOCX, TXT."
        )

    # 2. Read content and validate file size
    content = await file.read()
    file_size = len(content)
    if file_size > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds maximum limit of 10MB."
        )

    tenant_id = _get_tenant_id_from_user(current_user)
    
    # 3. Verify assistant existence & tenancy
    await _verify_assistant(db, tenant_id, assistant_id)

    # 4. Check duplicate filename for this assistant
    dup_res = await db.execute(
        select(Document).where(
            Document.assistant_id == assistant_id,
            Document.filename == filename
        )
    )
    if dup_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This file already exists in this assistant's knowledge base."
        )

    # 5. Check resource quotas
    await _check_document_quota(db, tenant_id)

    # 6. Upload file to MinIO
    doc_id = uuid.uuid4()
    storage_key = f"tenant/{tenant_id}/docs/{doc_id}/{filename}"
    try:
        storage_service.upload_file(
            object_name=storage_key,
            data=io.BytesIO(content),
            length=file_size,
            content_type=file.content_type or "application/octet-stream"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Storage upload failed: {str(e)}"
        )

    # 7. Create Document record
    document = Document(
        id=doc_id,
        tenant_id=tenant_id,
        assistant_id=assistant_id,
        filename=filename,
        storage_key=storage_key,
        file_type=suffix,
        status="pending",
        doc_metadata={}
    )
    db.add(document)
    await db.commit()
    await set_tenant_context(db, str(tenant_id))
    await db.refresh(document)

    # 8. Dispatch background Celery task
    task = ingest_document.delay(str(doc_id))

    # Store celery task id in metadata for potential cancellation
    from sqlalchemy.orm.attributes import flag_modified
    document.doc_metadata = {**document.doc_metadata, "celery_task_id": task.id}
    flag_modified(document, "doc_metadata")
    await db.commit()

    return document

@router.post("/url", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def ingest_url(
    payload: URLIngestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("owner", "admin")),
):
    """
    Submit a public URL to be crawled and ingested into the assistant's knowledge base.
    Restricted to owners and admins.
    """
    tenant_id = _get_tenant_id_from_user(current_user)
    
    # 1. Verify assistant existence & tenancy
    await _verify_assistant(db, tenant_id, payload.assistant_id)

    # 2. Check duplicate URL (stored in filename)
    url_str = str(payload.url)
    dup_res = await db.execute(
        select(Document).where(
            Document.assistant_id == payload.assistant_id,
            Document.filename == url_str
        )
    )
    if dup_res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This file already exists in this assistant's knowledge base."
        )

    # 3. Check resource quotas
    await _check_document_quota(db, tenant_id)

    # 4. Synchronous pre-flight URL validation
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url_str, follow_redirects=True)
            if response.status_code < 200 or response.status_code >= 300:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This URL could not be reached or requires authentication."
                )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This URL could not be reached or requires authentication."
        )

    # 5. Create Document record
    doc_id = uuid.uuid4()
    document = Document(
        id=doc_id,
        tenant_id=tenant_id,
        assistant_id=payload.assistant_id,
        filename=url_str,
        storage_key="url",
        file_type="url",
        status="pending",
        doc_metadata={}
    )
    db.add(document)
    await db.commit()
    await set_tenant_context(db, str(tenant_id))
    await db.refresh(document)

    # 6. Dispatch background Celery task
    task = ingest_document.delay(str(doc_id))

    # Store celery task id in metadata for potential cancellation
    from sqlalchemy.orm.attributes import flag_modified
    document.doc_metadata = {**document.doc_metadata, "celery_task_id": task.id}
    flag_modified(document, "doc_metadata")
    await db.commit()

    return document

@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    assistant_id: uuid.UUID | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("owner", "admin", "member")),
):
    """
    List documents for a tenant, optionally filtered by assistant.
    """
    tenant_id = _get_tenant_id_from_user(current_user)
    
    stmt = select(Document).where(Document.tenant_id == tenant_id)
    if assistant_id is not None:
        stmt = stmt.where(Document.assistant_id == assistant_id)
        
    result = await db.execute(stmt)
    return list(result.scalars().all())

@router.get("/{id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("owner", "admin", "member")),
):
    """
    Get the polling status of a document ingestion.
    """
    tenant_id = _get_tenant_id_from_user(current_user)
    
    result = await db.execute(
        select(Document).where(
            Document.id == id,
            Document.tenant_id == tenant_id
        )
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    return document


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("owner", "admin")),
):
    """
    Delete a document.
    Cancels in-flight ingestion if status is pending/processing.
    Removes storage objects from MinIO and vector chunks from ChromaDB.
    """
    tenant_id = _get_tenant_id_from_user(current_user)

    # 1. Fetch document and verify tenancy
    result = await db.execute(
        select(Document).where(
            Document.id == id,
            Document.tenant_id == tenant_id
        )
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    # 2. Cancel in-flight ingestion task if processing or pending
    if document.status in ("pending", "processing"):
        task_id = (document.doc_metadata or {}).get("celery_task_id")
        if task_id:
            try:
                celery_app.control.revoke(task_id, terminate=True)
            except Exception:
                pass

    # 3. Clean up external resources (MinIO storage and ChromaDB vectors)
    cleanup_errors = []

    # Only delete from MinIO if it's a file upload (not a URL)
    if document.storage_key and document.storage_key != "url":
        try:
            await asyncio.to_thread(storage_service.delete_file, document.storage_key)
        except Exception as exc:
            cleanup_errors.append(f"MinIO cleanup failed: {exc}")

    # Delete vectors from ChromaDB
    try:
        await asyncio.to_thread(
            chroma_client.delete_document_vectors,
            str(tenant_id),
            str(document.id)
        )
    except Exception as exc:
        cleanup_errors.append(f"ChromaDB cleanup failed: {exc}")

    if cleanup_errors:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document deletion aborted because associated storage cleanup failed: {', '.join(cleanup_errors)}"
        )

    # 4. Delete document record from DB
    await db.delete(document)
    await db.commit()

