import pytest
import time
import uuid
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
from sqlalchemy import text

from app.db.session import SessionLocal, enable_rls_bypass, set_tenant_context
from app.models.assistant import Assistant
from app.models.document import Document

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
async def test_embed_code_retrieval_performance(client: AsyncClient, registered_owner):
    tenant_uuid = uuid.UUID(registered_owner["tenant_id"])
    async with SessionLocal() as session:
        await enable_rls_bypass(session)
        assistant = Assistant(
            tenant_id=tenant_uuid,
            name="Perf Bot",
            system_prompt="system",
            is_active=True
        )
        session.add(assistant)
        await session.commit()
        assistant_id = assistant.id

    start_time = time.perf_counter()
    response = await client.get(
        f"/api/v1/assistants/{assistant_id}/embed",
        headers={
            "Authorization": f"Bearer {registered_owner['access_token']}",
            "X-Tenant-ID": registered_owner["tenant_id"]
        }
    )
    end_time = time.perf_counter()
    duration = end_time - start_time
    
    assert response.status_code == 200
    # Threshold: embed code retrieval within 1 second
    assert duration < 1.0

@pytest.mark.asyncio
async def test_document_status_freshness_performance(client: AsyncClient, registered_owner, sample_assistant):
    tenant_uuid = uuid.UUID(registered_owner["tenant_id"])
    async with SessionLocal() as session:
        await enable_rls_bypass(session)
        doc = Document(
            tenant_id=tenant_uuid,
            assistant_id=sample_assistant,
            filename="perf-status.txt",
            storage_key="test-key",
            file_type="txt",
            status="processing"
        )
        session.add(doc)
        await session.commit()
        doc_id = doc.id

    start_time = time.perf_counter()
    response = await client.get(
        f"/api/v1/documents/{doc_id}/status",
        headers={
            "Authorization": f"Bearer {registered_owner['access_token']}",
            "X-Tenant-ID": registered_owner["tenant_id"]
        }
    )
    end_time = time.perf_counter()
    duration = end_time - start_time
    
    assert response.status_code == 200
    # Threshold: status freshness within 5 seconds (API response must be fast, e.g., < 0.5s)
    assert duration < 0.5

@pytest.mark.asyncio
async def test_document_index_removal_performance(client: AsyncClient, registered_owner, sample_assistant):
    tenant_uuid = uuid.UUID(registered_owner["tenant_id"])
    async with SessionLocal() as session:
        await enable_rls_bypass(session)
        doc = Document(
            tenant_id=tenant_uuid,
            assistant_id=sample_assistant,
            filename="perf-delete.txt",
            storage_key="test-key",
            file_type="txt",
            status="ready"
        )
        session.add(doc)
        await session.commit()
        doc_id = doc.id

    with patch("app.api.v1.endpoints.documents.storage_service.delete_file") as mock_delete_file, \
         patch("app.api.v1.endpoints.documents.chroma_client.delete_document_vectors") as mock_delete_vectors:
        
        start_time = time.perf_counter()
        response = await client.delete(
            f"/api/v1/documents/{doc_id}",
            headers={
                "Authorization": f"Bearer {registered_owner['access_token']}",
                "X-Tenant-ID": registered_owner["tenant_id"]
            }
        )
        end_time = time.perf_counter()
        duration = end_time - start_time
        
        assert response.status_code == 204
        # Threshold: document index removal within 30 seconds (API response / cleanup must be < 2s)
        assert duration < 2.0
