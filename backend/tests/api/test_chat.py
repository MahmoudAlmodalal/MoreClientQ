import pytest
import jwt
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient
from sqlalchemy import text, select

from app.db.session import SessionLocal, enable_rls_bypass
from app.core.config import settings
from app.models.tenant import Tenant
from app.models.assistant import Assistant
from app.models.conversation import Conversation
from app.models.message import Message
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

@pytest_asyncio.fixture(autouse=True)
async def cleanup_chat_db():
    async with SessionLocal() as session:
        await enable_rls_bypass(session)
        await session.execute(text("TRUNCATE TABLE messages, conversations, assistants, tenants CASCADE"))
        await session.commit()
    yield
    async with SessionLocal() as session:
        await enable_rls_bypass(session)
        await session.execute(text("TRUNCATE TABLE messages, conversations, assistants, tenants CASCADE"))
        await session.commit()

@pytest.mark.asyncio
async def test_chat_endpoint_success(client: AsyncClient):
    async with SessionLocal() as db:
        await enable_rls_bypass(db)
        tenant = Tenant(
            slug="acmetest",
            name="Acme Test Corp",
            plan="pro",
            is_active=True,
            monthly_quota=100000,
            used_quota=0,
            settings={"token_quota_hourly": 5000}
        )
        db.add(tenant)
        await db.flush()
        
        assistant = Assistant(
            tenant_id=tenant.id,
            name="Test Bot",
            system_prompt="You are a helpful assistant.",
            model="gpt-4o",
            temperature=0.7,
            max_tokens=1000,
            is_active=True
        )
        db.add(assistant)
        await db.commit()
        
        tenant_id_str = str(tenant.id)
        assistant_id_str = str(assistant.id)

    token = _make_access_token("owner", tenant_id_str)
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": tenant_id_str,
    }

    mock_source = MagicMock()
    mock_source.document_id = uuid.uuid4()
    mock_source.chunk_text = "Chroma KB chunk info"
    mock_source.score = 0.9
    mock_source.model_dump.return_value = {
        "document_id": str(mock_source.document_id),
        "chunk_text": "Chroma KB chunk info",
        "score": 0.9
    }

    mock_llm_response = MagicMock()
    mock_llm_response.choices = [
        MagicMock(message=MagicMock(content="Grounded response text"))
    ]
    mock_llm_response.usage = MagicMock(total_tokens=150)
    mock_llm_response.model = "gpt-4o"

    with patch("app.services.rag.chroma_client.chroma_client.retrieve", new_callable=AsyncMock) as mock_retrieve, \
         patch("app.services.llm_service.complete_with_fallback", new_callable=AsyncMock) as mock_complete:
        
        mock_retrieve.return_value = [mock_source]
        mock_complete.return_value = mock_llm_response

        payload = {
            "assistant_id": assistant_id_str,
            "message": "Hello, how can you help me?"
        }

        response = await client.post("/api/v1/chat", json=payload, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "conversation_id" in data
        assert "message_id" in data
        assert data["content"] == "Grounded response text"
        assert data["tokens_used"] == 150
        assert len(data["sources"]) == 1
        assert data["sources"][0]["chunk_text"] == "Chroma KB chunk info"
        assert data["model_used"] == "gpt-4o"
        assert response.headers.get("Cache-Control") == "no-store"

        async with SessionLocal() as db:
            await enable_rls_bypass(db)
            conv_id = data["conversation_id"]
            msgs = (await db.execute(
                select(Message).where(Message.conversation_id == uuid.UUID(conv_id))
            )).scalars().all()
            
            assert len(msgs) == 2
            user_msg = next(m for m in msgs if m.role == "user")
            asst_msg = next(m for m in msgs if m.role == "assistant")
            
            assert user_msg.content == "Hello, how can you help me?"
            assert asst_msg.content == "Grounded response text"
            assert asst_msg.tokens_used == 150

@pytest.mark.asyncio
async def test_chat_handoff_keyword(client: AsyncClient):
    async with SessionLocal() as db:
        await enable_rls_bypass(db)
        tenant = Tenant(
            slug="acmetest2",
            name="Acme Test Corp 2",
            plan="pro",
            is_active=True,
            monthly_quota=100000,
            used_quota=0,
            settings={}
        )
        db.add(tenant)
        await db.flush()
        
        assistant = Assistant(
            tenant_id=tenant.id,
            name="Test Bot 2",
            system_prompt="You are a helpful assistant.",
            model="gpt-4o",
            temperature=0.7,
            max_tokens=1000,
            is_active=True
        )
        db.add(assistant)
        await db.commit()
        
        tenant_id_str = str(tenant.id)
        assistant_id_str = str(assistant.id)

    token = _make_access_token("owner", tenant_id_str)
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": tenant_id_str,
    }

    payload = {
        "assistant_id": assistant_id_str,
        "message": "speak to human"
    }

    async def mock_trigger_handoff(t_id, c_id, a_id, *args, **kwargs):
        async with SessionLocal() as db_session:
            await enable_rls_bypass(db_session)
            await db_session.execute(
                text("UPDATE conversations SET status = 'handoff' WHERE id = :conv_id"),
                {"conv_id": c_id}
            )
            await db_session.commit()

    with patch("app.services.handoff_service.is_handoff_trigger", return_value=True), \
         patch("app.services.handoff_service.trigger_handoff", side_effect=mock_trigger_handoff):
        response = await client.post("/api/v1/chat", json=payload, headers=headers)
        assert response.status_code == 409
        assert response.json()["detail"] == "Conversation is in handoff mode; AI responses are suspended"

    async with SessionLocal() as db:
        await enable_rls_bypass(db)
        conversations = (await db.execute(
            select(Conversation).where(Conversation.tenant_id == tenant.id)
        )).scalars().all()
        assert len(conversations) == 1
        assert conversations[0].status == "handoff"

@pytest.mark.asyncio
async def test_chat_quota_exceeded(client: AsyncClient):
    async with SessionLocal() as db:
        await enable_rls_bypass(db)
        tenant = Tenant(
            slug="acmetest3",
            name="Acme Test Corp 3",
            plan="pro",
            is_active=True,
            monthly_quota=100000,
            used_quota=0,
            settings={"token_quota_hourly": 0}
        )
        db.add(tenant)
        await db.flush()
        
        assistant = Assistant(
            tenant_id=tenant.id,
            name="Test Bot 3",
            system_prompt="You are a helpful assistant.",
            model="gpt-4o",
            temperature=0.7,
            max_tokens=1000,
            is_active=True
        )
        db.add(assistant)
        await db.commit()
        
        tenant_id_str = str(tenant.id)
        assistant_id_str = str(assistant.id)

    token = _make_access_token("owner", tenant_id_str)
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Tenant-ID": tenant_id_str,
    }

    payload = {
        "assistant_id": assistant_id_str,
        "message": "Hello, how can you help me?"
    }

    response = await client.post("/api/v1/chat", json=payload, headers=headers)
    assert response.status_code == 429
    assert response.json()["detail"] == "Token quota exceeded for this billing period"
