import pytest
import jwt
import uuid
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient
from unittest.mock import MagicMock, patch
from sqlalchemy import text, select

from app.db.session import SessionLocal, enable_rls_bypass, set_tenant_context
from app.core.config import settings
from app.models.tenant import Tenant
from app.models.user import User
from app.models.assistant import Assistant
from app.models.document import Document
from app.models.conversation import Conversation

import pytest_asyncio


def _make_access_token(role: str, tenant_id: str) -> str:
    payload = {
        "sub": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "tenant_slug": "acme",
        "role": role,
        "type": "access",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

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
    unique_id = uuid.uuid4().hex[:8]
    tenant_slug = f"acme{unique_id}"
    owner_email = f"owner-{unique_id}@acme.com"
    payload = {
        "tenant_slug": tenant_slug,
        "tenant_name": "Acme Corp",
        "owner_email": owner_email,
        "owner_password": "securepassword123",
        "owner_full_name": "Acme Owner"
    }
    reg_res = await client.post("/api/v1/auth/register", json=payload)
    assert reg_res.status_code == 201
    tenant_id = reg_res.json()["tenant"]["id"]
    login_res = await client.post("/api/v1/auth/login", json={
        "email": owner_email,
        "password": "securepassword123"
    })
    assert login_res.status_code == 200
    return {
        "tenant_id": tenant_id,
        "access_token": login_res.json()["access_token"],
        "tenant_slug": tenant_slug
    }

@pytest.mark.asyncio
async def test_list_assistants_empty(client: AsyncClient, registered_owner):
    response = await client.get(
        "/api/v1/assistants",
        headers={
            "Authorization": f"Bearer {registered_owner['access_token']}",
            "X-Tenant-ID": registered_owner["tenant_id"]
        }
    )
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_create_assistant_success(client: AsyncClient, registered_owner):
    payload = {
        "name": "Customer Support Bot",
        "system_prompt": "You are a helpful customer support bot.",
        "model": "gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": 1024
    }
    response = await client.post(
        "/api/v1/assistants",
        headers={
            "Authorization": f"Bearer {registered_owner['access_token']}",
            "X-Tenant-ID": registered_owner["tenant_id"]
        },
        json=payload
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Customer Support Bot"
    assert data["system_prompt"] == "You are a helpful customer support bot."
    assert data["model"] == "gpt-4o-mini"
    assert data["temperature"] == 0.7
    assert data["max_tokens"] == 1024
    assert data["is_active"] is True
    assert "id" in data

    # Verify RLS and DB insertion
    async with SessionLocal() as session:
        await set_tenant_context(session, registered_owner["tenant_id"])
        result = await session.execute(
            select(Assistant).where(Assistant.id == uuid.UUID(data["id"]))
        )
        assistant = result.scalar_one_or_none()
        assert assistant is not None
        assert assistant.name == "Customer Support Bot"

@pytest.mark.asyncio
async def test_create_assistant_name_validation(client: AsyncClient, registered_owner):
    # Test blank name validation
    payload = {
        "name": "",  # Empty name
        "system_prompt": "Prompt",
        "model": "gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": 1024
    }
    response = await client.post(
        "/api/v1/assistants",
        headers={
            "Authorization": f"Bearer {registered_owner['access_token']}",
            "X-Tenant-ID": registered_owner["tenant_id"]
        },
        json=payload
    )
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_create_assistant_whitespace_name_validation(client: AsyncClient, registered_owner):
    payload = {
        "name": "   ",
        "system_prompt": "Prompt",
        "model": "gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": 1024
    }
    response = await client.post(
        "/api/v1/assistants",
        headers={
            "Authorization": f"Bearer {registered_owner['access_token']}",
            "X-Tenant-ID": registered_owner["tenant_id"]
        },
        json=payload
    )
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_create_assistant_quota_limit(client: AsyncClient, registered_owner):
    # Plan is "starter", which has max_assistants=1.
    # First assistant creation should succeed.
    payload = {
        "name": "First Bot",
        "system_prompt": "Prompt",
        "model": "gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": 1024
    }
    response1 = await client.post(
        "/api/v1/assistants",
        headers={
            "Authorization": f"Bearer {registered_owner['access_token']}",
            "X-Tenant-ID": registered_owner["tenant_id"]
        },
        json=payload
    )
    assert response1.status_code == 201

    # Second assistant creation should fail due to quota limit.
    response2 = await client.post(
        "/api/v1/assistants",
        headers={
            "Authorization": f"Bearer {registered_owner['access_token']}",
            "X-Tenant-ID": registered_owner["tenant_id"]
        },
        json={**payload, "name": "Second Bot"}
    )
    assert response2.status_code == 400
    assert "Limit of 1 assistants exceeded for your plan." in response2.json()["detail"]

@pytest.mark.asyncio
async def test_get_assistant_details(client: AsyncClient, registered_owner):
    # Create assistant
    create_res = await client.post(
        "/api/v1/assistants",
        headers={
            "Authorization": f"Bearer {registered_owner['access_token']}",
            "X-Tenant-ID": registered_owner["tenant_id"]
        },
        json={"name": "Details Bot"}
    )
    assert create_res.status_code == 201
    assistant_id = create_res.json()["id"]

    # Get details
    response = await client.get(
        f"/api/v1/assistants/{assistant_id}",
        headers={
            "Authorization": f"Bearer {registered_owner['access_token']}",
            "X-Tenant-ID": registered_owner["tenant_id"]
        }
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Details Bot"

@pytest.mark.asyncio
async def test_update_assistant(client: AsyncClient, registered_owner):
    # Create assistant
    create_res = await client.post(
        "/api/v1/assistants",
        headers={
            "Authorization": f"Bearer {registered_owner['access_token']}",
            "X-Tenant-ID": registered_owner["tenant_id"]
        },
        json={"name": "Original Name", "temperature": 0.7}
    )
    assert create_res.status_code == 201
    assistant_id = create_res.json()["id"]

    # Update assistant
    update_res = await client.patch(
        f"/api/v1/assistants/{assistant_id}",
        headers={
            "Authorization": f"Bearer {registered_owner['access_token']}",
            "X-Tenant-ID": registered_owner["tenant_id"]
        },
        json={"name": "Updated Name", "temperature": 0.5}
    )
    assert update_res.status_code == 200
    data = update_res.json()
    assert data["name"] == "Updated Name"
    assert data["temperature"] == 0.5

@pytest.mark.asyncio
async def test_delete_assistant_active_conversations_blocked(client: AsyncClient, registered_owner):
    tenant_uuid = uuid.UUID(registered_owner["tenant_id"])
    
    # Create assistant and an active conversation
    async with SessionLocal() as session:
        await enable_rls_bypass(session)
        assistant = Assistant(
            tenant_id=tenant_uuid,
            name="Active Assistant",
            system_prompt="system",
            is_active=True
        )
        session.add(assistant)
        await session.flush()
        
        conversation = Conversation(
            tenant_id=tenant_uuid,
            assistant_id=assistant.id,
            session_token="session-123",
            status="active"
        )
        session.add(conversation)
        await session.commit()
        assistant_id = assistant.id

    # Attempt to delete
    response = await client.delete(
        f"/api/v1/assistants/{assistant_id}",
        headers={
            "Authorization": f"Bearer {registered_owner['access_token']}",
            "X-Tenant-ID": registered_owner["tenant_id"]
        }
    )
    assert response.status_code == 409
    assert "This assistant has 1 active conversations. Resolve or end them before deleting." in response.json()["detail"]

@pytest.mark.asyncio
async def test_delete_assistant_cascade_cleanup(client: AsyncClient, registered_owner):
    tenant_uuid = uuid.UUID(registered_owner["tenant_id"])
    
    # Create assistant, conversation (resolved/inactive), and a document
    async with SessionLocal() as session:
        await enable_rls_bypass(session)
        assistant = Assistant(
            tenant_id=tenant_uuid,
            name="Clean Bot",
            system_prompt="system",
            is_active=True
        )
        session.add(assistant)
        await session.flush()
        
        conversation = Conversation(
            tenant_id=tenant_uuid,
            assistant_id=assistant.id,
            session_token="session-456",
            status="ended"  # Non-active conversation
        )
        session.add(conversation)
        
        doc = Document(
            tenant_id=tenant_uuid,
            assistant_id=assistant.id,
            filename="test_doc.pdf",
            storage_key="test-storage-key",
            file_type="pdf",
            status="ready"
        )
        session.add(doc)
        await session.commit()
        assistant_id = assistant.id
        doc_id = doc.id

    # Patch storage and vector deletes
    with patch("app.services.assistant.storage_service.delete_file") as mock_delete_file, \
         patch("app.services.assistant.chroma_client.delete_document_vectors") as mock_delete_vectors:
        
        response = await client.delete(
            f"/api/v1/assistants/{assistant_id}",
            headers={
                "Authorization": f"Bearer {registered_owner['access_token']}",
                "X-Tenant-ID": registered_owner["tenant_id"]
            }
        )
        assert response.status_code == 204
        
        # Verify mocked cleanup calls
        mock_delete_file.assert_called_once_with("test-storage-key")
        mock_delete_vectors.assert_called_once_with(registered_owner["tenant_id"], str(doc_id))

    # Verify DB rows are removed
    async with SessionLocal() as session:
        await enable_rls_bypass(session)
        ast_check = await session.get(Assistant, assistant_id)
        assert ast_check is None
        
        doc_check = await session.get(Document, doc_id)
        assert doc_check is None

@pytest.mark.asyncio
async def test_delete_assistant_cascade_cleanup_skips_minio_for_url_documents(client: AsyncClient, registered_owner):
    tenant_uuid = uuid.UUID(registered_owner["tenant_id"])

    async with SessionLocal() as session:
        await enable_rls_bypass(session)
        assistant = Assistant(
            tenant_id=tenant_uuid,
            name="URL Clean Bot",
            system_prompt="system",
            is_active=True
        )
        session.add(assistant)
        await session.flush()

        doc = Document(
            tenant_id=tenant_uuid,
            assistant_id=assistant.id,
            filename="https://example.com/docs",
            storage_key="url",
            file_type="url",
            status="ready"
        )
        session.add(doc)
        await session.commit()
        assistant_id = assistant.id
        doc_id = doc.id

    with patch("app.services.assistant.storage_service.delete_file") as mock_delete_file, \
         patch("app.services.assistant.chroma_client.delete_document_vectors") as mock_delete_vectors:
        response = await client.delete(
            f"/api/v1/assistants/{assistant_id}",
            headers={
                "Authorization": f"Bearer {registered_owner['access_token']}",
                "X-Tenant-ID": registered_owner["tenant_id"]
            }
        )
        assert response.status_code == 204
        mock_delete_file.assert_not_called()
        mock_delete_vectors.assert_called_once_with(registered_owner["tenant_id"], str(doc_id))

    async with SessionLocal() as session:
        await enable_rls_bypass(session)
        ast_check = await session.get(Assistant, assistant_id)
        doc_check = await session.get(Document, doc_id)
        assert ast_check is None
        assert doc_check is None

@pytest.mark.asyncio
async def test_delete_assistant_cleanup_failure_aborts_delete(client: AsyncClient, registered_owner):
    tenant_uuid = uuid.UUID(registered_owner["tenant_id"])

    async with SessionLocal() as session:
        await enable_rls_bypass(session)
        assistant = Assistant(
            tenant_id=tenant_uuid,
            name="Cleanup Fail Bot",
            system_prompt="system",
            is_active=True
        )
        session.add(assistant)
        await session.flush()

        doc = Document(
            tenant_id=tenant_uuid,
            assistant_id=assistant.id,
            filename="cleanup-fail.pdf",
            storage_key="cleanup-fail-key",
            file_type="pdf",
            status="ready"
        )
        session.add(doc)
        await session.commit()
        assistant_id = assistant.id

    with patch("app.services.assistant.storage_service.delete_file", side_effect=RuntimeError("minio down")) as mock_delete_file, \
         patch("app.services.assistant.chroma_client.delete_document_vectors") as mock_delete_vectors:
        response = await client.delete(
            f"/api/v1/assistants/{assistant_id}",
            headers={
                "Authorization": f"Bearer {registered_owner['access_token']}",
                "X-Tenant-ID": registered_owner["tenant_id"]
            }
        )
        assert response.status_code == 500
        assert "Assistant deletion aborted because associated storage cleanup failed." in response.json()["detail"]
        mock_delete_file.assert_called_once_with("cleanup-fail-key")
        mock_delete_vectors.assert_called_once()

    async with SessionLocal() as session:
        await enable_rls_bypass(session)
        ast_check = await session.get(Assistant, assistant_id)
        assert ast_check is not None

@pytest.mark.asyncio
async def test_get_widget_embed_code(client: AsyncClient, registered_owner):
    # Create assistant
    create_res = await client.post(
        "/api/v1/assistants",
        headers={
            "Authorization": f"Bearer {registered_owner['access_token']}",
            "X-Tenant-ID": registered_owner["tenant_id"]
        },
        json={"name": "Embed Bot"}
    )
    assert create_res.status_code == 201
    assistant_id = create_res.json()["id"]

    # Get embed code
    response = await client.get(
        f"/api/v1/assistants/{assistant_id}/embed",
        headers={
            "Authorization": f"Bearer {registered_owner['access_token']}",
            "X-Tenant-ID": registered_owner["tenant_id"]
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "snippet" in data
    assert data["snippet"].startswith(f'<script src="{settings.WIDGET_BASE_URL}/widget.js"')
    assert f'data-assistant="{assistant_id}"' in data["snippet"]
    assert 'data-theme="light"' in data["snippet"]
    assert 'data-position="bottom-right"' in data["snippet"]
    assert "widget.js" in data["snippet"]


@pytest.mark.asyncio
async def test_get_widget_embed_code_rejects_member(client: AsyncClient, registered_owner):
    create_res = await client.post(
        "/api/v1/assistants",
        headers={
            "Authorization": f"Bearer {registered_owner['access_token']}",
            "X-Tenant-ID": registered_owner["tenant_id"]
        },
        json={"name": "Member Blocked Embed Bot"}
    )
    assert create_res.status_code == 201
    assistant_id = create_res.json()["id"]
    member_token = _make_access_token("member", registered_owner["tenant_id"])

    response = await client.get(
        f"/api/v1/assistants/{assistant_id}/embed",
        headers={
            "Authorization": f"Bearer {member_token}",
            "X-Tenant-ID": registered_owner["tenant_id"]
        }
    )

    assert response.status_code == 403

@pytest.mark.asyncio
async def test_create_assistant_concurrency(client: AsyncClient, registered_owner):
    # Plan is "starter", which has max_assistants=1.
    # Send 3 requests concurrently. Only 1 should succeed with 201, other 2 should fail with 400.
    payload = {
        "name": "Concurrent Bot",
        "system_prompt": "Prompt",
        "model": "gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": 1024
    }

    import asyncio

    async def make_request(i):
        return await client.post(
            "/api/v1/assistants",
            headers={
                "Authorization": f"Bearer {registered_owner['access_token']}",
                "X-Tenant-ID": registered_owner["tenant_id"]
            },
            json={**payload, "name": f"Concurrent Bot {i}"}
        )

    responses = await asyncio.gather(*(make_request(i) for i in range(3)))

    successes = [r for r in responses if r.status_code == 201]
    quota_exceeded = [r for r in responses if r.status_code == 400 and "exceeded" in r.json()["detail"]]

    assert len(successes) == 1
    assert len(quota_exceeded) == 2
