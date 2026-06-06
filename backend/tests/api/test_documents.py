import pytest
import uuid
import io
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
from sqlalchemy import select, text

from app.db.session import SessionLocal, enable_rls_bypass, set_tenant_context
from app.models.assistant import Assistant
from app.models.document import Document
from app.models.tenant import Tenant

async def _truncate_all():
    async with SessionLocal() as session:
        await enable_rls_bypass(session)
        await session.execute(text("TRUNCATE TABLE users, tenants, assistants, documents, conversations CASCADE"))
        await session.commit()

@pytest_asyncio.fixture(autouse=True)
async def cleanup_db():
    await _truncate_all()
    yield
    await _truncate_all()

@pytest_asyncio.fixture
async def registered_owner(client: AsyncClient):
    payload = {
        "tenant_slug": "acme",
        "tenant_name": "Acme Corp",
        "owner_email": "owner@acme.com",
        "owner_password": "securepassword123",
        "owner_full_name": "Acme Owner"
    }
    reg_res = await client.post("/api/v1/auth/register", json=payload)
    assert reg_res.status_code == 201
    tenant_id = reg_res.json()["tenant"]["id"]
    login_res = await client.post("/api/v1/auth/login", json={
        "email": "owner@acme.com",
        "password": "securepassword123"
    })
    assert login_res.status_code == 200
    return {
        "tenant_id": tenant_id,
        "access_token": login_res.json()["access_token"],
        "tenant_slug": "acme"
    }

@pytest_asyncio.fixture
async def sample_assistant(registered_owner):
    tenant_uuid = uuid.UUID(registered_owner["tenant_id"])
    async with SessionLocal() as session:
        await enable_rls_bypass(session)
        assistant = Assistant(
            tenant_id=tenant_uuid,
            name="Test Bot",
            system_prompt="system",
            is_active=True
        )
        session.add(assistant)
        await session.commit()
        return assistant.id

@pytest.mark.asyncio
async def test_upload_document_success(client: AsyncClient, registered_owner, sample_assistant):
    file_content = b"Hello, this is a test document with some content to verify chunking and embedding."
    file_io = io.BytesIO(file_content)

    with patch("app.api.v1.endpoints.documents.storage_service.upload_file") as mock_upload, \
         patch("app.api.v1.endpoints.documents.ingest_document.delay") as mock_celery:
        
        mock_upload.return_value = "tenant/acme/docs/some-uuid/test.txt"
        mock_celery.return_value.id = "some-celery-task-id"

        response = await client.post(
            "/api/v1/documents/upload",
            headers={
                "Authorization": f"Bearer {registered_owner['access_token']}",
                "X-Tenant-ID": registered_owner["tenant_id"]
            },
            data={"assistant_id": str(sample_assistant)},
            files={"file": ("test.txt", file_io, "text/plain")}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "test.txt"
        assert data["file_type"] == "txt"
        assert data["status"] == "pending"
        assert data["chunk_count"] is None
        assert "id" in data

        mock_upload.assert_called_once()
        mock_celery.assert_called_once_with(data["id"])

        # Check in DB
        async with SessionLocal() as session:
            await set_tenant_context(session, registered_owner["tenant_id"])
            result = await session.execute(
                select(Document).where(Document.id == uuid.UUID(data["id"]))
            )
            doc = result.scalar_one_or_none()
            assert doc is not None
            assert doc.filename == "test.txt"
            assert doc.file_type == "txt"

@pytest.mark.asyncio
async def test_upload_document_unsupported_type(client: AsyncClient, registered_owner, sample_assistant):
    file_io = io.BytesIO(b"print('hello')")
    response = await client.post(
        "/api/v1/documents/upload",
        headers={
            "Authorization": f"Bearer {registered_owner['access_token']}",
            "X-Tenant-ID": registered_owner["tenant_id"]
        },
        data={"assistant_id": str(sample_assistant)},
        files={"file": ("test.py", file_io, "text/x-python")}
    )
    assert response.status_code == 400
    assert "Unsupported file type. Allowed: PDF, DOCX, TXT." in response.json()["detail"]

@pytest.mark.asyncio
async def test_upload_document_duplicate_filename(client: AsyncClient, registered_owner, sample_assistant):
    # Setup first document in DB
    tenant_uuid = uuid.UUID(registered_owner["tenant_id"])
    async with SessionLocal() as session:
        await enable_rls_bypass(session)
        doc = Document(
            tenant_id=tenant_uuid,
            assistant_id=sample_assistant,
            filename="duplicate.txt",
            storage_key="test-key",
            file_type="txt",
            status="ready"
        )
        session.add(doc)
        await session.commit()

    file_io = io.BytesIO(b"Hello world duplicate test")
    response = await client.post(
        "/api/v1/documents/upload",
        headers={
            "Authorization": f"Bearer {registered_owner['access_token']}",
            "X-Tenant-ID": registered_owner["tenant_id"]
        },
        data={"assistant_id": str(sample_assistant)},
        files={"file": ("duplicate.txt", file_io, "text/plain")}
    )
    assert response.status_code == 400
    assert "This file already exists in this assistant's knowledge base." in response.json()["detail"]

@pytest.mark.asyncio
async def test_upload_document_quota_exceeded(client: AsyncClient, registered_owner, sample_assistant):
    # Plan is starter -> max 5 documents. Insert 5 documents
    tenant_uuid = uuid.UUID(registered_owner["tenant_id"])
    async with SessionLocal() as session:
        await enable_rls_bypass(session)
        for i in range(5):
            doc = Document(
                tenant_id=tenant_uuid,
                assistant_id=sample_assistant,
                filename=f"doc_{i}.txt",
                storage_key=f"test-key-{i}",
                file_type="txt",
                status="ready"
            )
            session.add(doc)
        await session.commit()

    file_io = io.BytesIO(b"Sixth document should fail")
    response = await client.post(
        "/api/v1/documents/upload",
        headers={
            "Authorization": f"Bearer {registered_owner['access_token']}",
            "X-Tenant-ID": registered_owner["tenant_id"]
        },
        data={"assistant_id": str(sample_assistant)},
        files={"file": ("doc_sixth.txt", file_io, "text/plain")}
    )
    assert response.status_code == 400
    assert "Limit of 5 documents exceeded for your plan." in response.json()["detail"]

@pytest.mark.asyncio
async def test_upload_document_storage_quota_exceeded_before_upload(client: AsyncClient, registered_owner, sample_assistant):
    tenant_uuid = uuid.UUID(registered_owner["tenant_id"])
    async with SessionLocal() as session:
        await enable_rls_bypass(session)
        tenant = await session.get(Tenant, tenant_uuid)
        tenant.plan = "pro"
        doc = Document(
            tenant_id=tenant_uuid,
            assistant_id=sample_assistant,
            filename="almost-full.txt",
            storage_key="tenant/acme/docs/almost-full.txt",
            file_type="txt",
            status="ready",
            doc_metadata={"file_size": 100 * 10 * 1024 * 1024 - 1}
        )
        session.add(doc)
        await session.commit()

    file_io = io.BytesIO(b"xx")
    with patch("app.api.v1.endpoints.documents.storage_service.upload_file") as mock_upload, \
         patch("app.api.v1.endpoints.documents.ingest_document.delay") as mock_celery:
        response = await client.post(
            "/api/v1/documents/upload",
            headers={
                "Authorization": f"Bearer {registered_owner['access_token']}",
                "X-Tenant-ID": registered_owner["tenant_id"]
            },
            data={"assistant_id": str(sample_assistant)},
            files={"file": ("overflow.txt", file_io, "text/plain")}
        )

        assert response.status_code == 400
        assert "storage quota exceeded" in response.json()["detail"]
        mock_upload.assert_not_called()
        mock_celery.assert_not_called()

    async with SessionLocal() as session:
        await enable_rls_bypass(session)
        result = await session.execute(
            select(Document).where(
                Document.tenant_id == tenant_uuid,
                Document.filename == "overflow.txt"
            )
        )
        assert result.scalar_one_or_none() is None

@pytest.mark.asyncio
async def test_upload_document_size_limit(client: AsyncClient, registered_owner, sample_assistant):
    # 10 MB limit + 1 byte
    too_large_content = b"a" * (10 * 1024 * 1024 + 1)
    file_io = io.BytesIO(too_large_content)

    response = await client.post(
        "/api/v1/documents/upload",
        headers={
            "Authorization": f"Bearer {registered_owner['access_token']}",
            "X-Tenant-ID": registered_owner["tenant_id"]
        },
        data={"assistant_id": str(sample_assistant)},
        files={"file": ("large.txt", file_io, "text/plain")}
    )
    assert response.status_code == 400
    assert "File size exceeds maximum limit of 10MB." in response.json()["detail"]

@pytest.mark.asyncio
async def test_ingest_url_success(client: AsyncClient, registered_owner, sample_assistant):
    payload = {
        "url": "https://example.com/docs",
        "assistant_id": str(sample_assistant)
    }

    with patch("app.api.v1.endpoints.documents.httpx.AsyncClient.get") as mock_get, \
         patch("app.api.v1.endpoints.documents.ingest_document.delay") as mock_celery:
        
        mock_get.return_value = MagicMock(status_code=200)
        mock_celery.return_value.id = "some-celery-task-id"

        response = await client.post(
            "/api/v1/documents/url",
            headers={
                "Authorization": f"Bearer {registered_owner['access_token']}",
                "X-Tenant-ID": registered_owner["tenant_id"]
            },
            json=payload
        )
        assert response.status_code == 201
        data = response.json()
        assert data["filename"] == "https://example.com/docs"
        assert data["file_type"] == "url"
        assert data["status"] == "pending"
        mock_get.assert_called_once()
        mock_celery.assert_called_once_with(data["id"])

@pytest.mark.asyncio
async def test_ingest_url_validation_failure(client: AsyncClient, registered_owner, sample_assistant):
    payload = {
        "url": "https://invalid-domain.xyz/docs",
        "assistant_id": str(sample_assistant)
    }

    with patch("app.api.v1.endpoints.documents.httpx.AsyncClient.get") as mock_get:
        mock_get.return_value = MagicMock(status_code=404)

        response = await client.post(
            "/api/v1/documents/url",
            headers={
                "Authorization": f"Bearer {registered_owner['access_token']}",
                "X-Tenant-ID": registered_owner["tenant_id"]
            },
            json=payload
        )
        assert response.status_code == 400
        assert "This URL could not be reached or requires authentication." in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_document_status(client: AsyncClient, registered_owner, sample_assistant):
    tenant_uuid = uuid.UUID(registered_owner["tenant_id"])
    async with SessionLocal() as session:
        await enable_rls_bypass(session)
        doc = Document(
            tenant_id=tenant_uuid,
            assistant_id=sample_assistant,
            filename="polling.txt",
            storage_key="test-polling-key",
            file_type="txt",
            status="processing"
        )
        session.add(doc)
        await session.commit()
        doc_id = doc.id

    response = await client.get(
        f"/api/v1/documents/{doc_id}/status",
        headers={
            "Authorization": f"Bearer {registered_owner['access_token']}",
            "X-Tenant-ID": registered_owner["tenant_id"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(doc_id)
    assert data["status"] == "processing"
    assert data["chunk_count"] is None

@pytest.mark.asyncio
async def test_list_documents(client: AsyncClient, registered_owner, sample_assistant):
    tenant_uuid = uuid.UUID(registered_owner["tenant_id"])
    async with SessionLocal() as session:
        await enable_rls_bypass(session)
        doc1 = Document(
            tenant_id=tenant_uuid,
            assistant_id=sample_assistant,
            filename="doc1.txt",
            storage_key="key1",
            file_type="txt",
            status="ready",
            chunk_count=10
        )
        doc2 = Document(
            tenant_id=tenant_uuid,
            assistant_id=sample_assistant,
            filename="doc2.txt",
            storage_key="key2",
            file_type="txt",
            status="ready",
            chunk_count=5
        )
        session.add(doc1)
        session.add(doc2)
        await session.commit()

    response = await client.get(
        f"/api/v1/documents?assistant_id={sample_assistant}",
        headers={
            "Authorization": f"Bearer {registered_owner['access_token']}",
            "X-Tenant-ID": registered_owner["tenant_id"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    filenames = [d["filename"] for d in data]
    assert "doc1.txt" in filenames
    assert "doc2.txt" in filenames

@pytest.mark.asyncio
async def test_delete_document_success(client: AsyncClient, registered_owner, sample_assistant):
    tenant_uuid = uuid.UUID(registered_owner["tenant_id"])
    async with SessionLocal() as session:
        await enable_rls_bypass(session)
        doc = Document(
            tenant_id=tenant_uuid,
            assistant_id=sample_assistant,
            filename="delete-me.txt",
            storage_key="tenant/acme/docs/delete-me.txt",
            file_type="txt",
            status="ready"
        )
        session.add(doc)
        await session.commit()
        doc_id = doc.id

    with patch("app.api.v1.endpoints.documents.storage_service.delete_file") as mock_delete_file, \
         patch("app.api.v1.endpoints.documents.chroma_client.delete_document_vectors") as mock_delete_vectors:
        
        response = await client.delete(
            f"/api/v1/documents/{doc_id}",
            headers={
                "Authorization": f"Bearer {registered_owner['access_token']}",
                "X-Tenant-ID": registered_owner["tenant_id"]
            }
        )
        assert response.status_code == 204
        
        mock_delete_file.assert_called_once_with("tenant/acme/docs/delete-me.txt")
        mock_delete_vectors.assert_called_once_with(registered_owner["tenant_id"], str(doc_id))

    async with SessionLocal() as session:
        await enable_rls_bypass(session)
        check_doc = await session.get(Document, doc_id)
        assert check_doc is None

@pytest.mark.asyncio
async def test_delete_document_processing_cancels_celery(client: AsyncClient, registered_owner, sample_assistant):
    tenant_uuid = uuid.UUID(registered_owner["tenant_id"])
    async with SessionLocal() as session:
        await enable_rls_bypass(session)
        doc = Document(
            tenant_id=tenant_uuid,
            assistant_id=sample_assistant,
            filename="processing.txt",
            storage_key="tenant/acme/docs/processing.txt",
            file_type="txt",
            status="processing",
            doc_metadata={"celery_task_id": "test-task-123"}
        )
        session.add(doc)
        await session.commit()
        doc_id = doc.id

    with patch("app.api.v1.endpoints.documents.celery_app.control.revoke") as mock_revoke, \
         patch("app.api.v1.endpoints.documents.storage_service.delete_file") as mock_delete_file, \
         patch("app.api.v1.endpoints.documents.chroma_client.delete_document_vectors") as mock_delete_vectors:
        
        response = await client.delete(
            f"/api/v1/documents/{doc_id}",
            headers={
                "Authorization": f"Bearer {registered_owner['access_token']}",
                "X-Tenant-ID": registered_owner["tenant_id"]
            }
        )
        assert response.status_code == 204
        
        mock_revoke.assert_called_once_with("test-task-123", terminate=True)
        mock_delete_file.assert_called_once_with("tenant/acme/docs/processing.txt")
        mock_delete_vectors.assert_called_once_with(registered_owner["tenant_id"], str(doc_id))

    async with SessionLocal() as session:
        await enable_rls_bypass(session)
        check_doc = await session.get(Document, doc_id)
        assert check_doc is None

@pytest.mark.asyncio
async def test_delete_document_cleanup_failure(client: AsyncClient, registered_owner, sample_assistant):
    tenant_uuid = uuid.UUID(registered_owner["tenant_id"])
    async with SessionLocal() as session:
        await enable_rls_bypass(session)
        doc = Document(
            tenant_id=tenant_uuid,
            assistant_id=sample_assistant,
            filename="fail.txt",
            storage_key="tenant/acme/docs/fail.txt",
            file_type="txt",
            status="ready"
        )
        session.add(doc)
        await session.commit()
        doc_id = doc.id

    with patch("app.api.v1.endpoints.documents.storage_service.delete_file", side_effect=Exception("MinIO down")), \
         patch("app.api.v1.endpoints.documents.chroma_client.delete_document_vectors") as mock_delete_vectors:
        
        response = await client.delete(
            f"/api/v1/documents/{doc_id}",
            headers={
                "Authorization": f"Bearer {registered_owner['access_token']}",
                "X-Tenant-ID": registered_owner["tenant_id"]
            }
        )
        assert response.status_code == 500
        assert "Document deletion aborted because associated storage cleanup failed" in response.json()["detail"]

    # Verify document is still in DB since delete was aborted
    async with SessionLocal() as session:
        await enable_rls_bypass(session)
        check_doc = await session.get(Document, doc_id)
        assert check_doc is not None

@pytest.mark.asyncio
async def test_delete_document_not_found(client: AsyncClient, registered_owner):
    fake_id = uuid.uuid4()
    response = await client.delete(
        f"/api/v1/documents/{fake_id}",
        headers={
            "Authorization": f"Bearer {registered_owner['access_token']}",
            "X-Tenant-ID": registered_owner["tenant_id"]
        }
    )
    assert response.status_code == 404
    assert "Document not found" in response.json()["detail"]
