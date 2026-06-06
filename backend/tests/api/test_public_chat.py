import pytest
import uuid
import json
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient

from app.services.llm_service import LLMUnavailableError

class MockAsyncIterator:
    def __init__(self, items):
        self.items = items

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self.items:
            raise StopAsyncIteration
        return self.items.pop(0)

@pytest.mark.asyncio
async def test_public_chat_endpoint_success(client: AsyncClient):
    session_id = str(uuid.uuid4())
    
    # Mock rate limit to allow and return count = 1
    mock_rate_limit = AsyncMock(return_value=(True, 1))
    
    # Mock LLM stream chunks
    chunk1 = MagicMock()
    chunk1.choices = [MagicMock()]
    chunk1.choices[0].delta.content = "Hello "
    
    chunk2 = MagicMock()
    chunk2.choices = [MagicMock()]
    chunk2.choices[0].delta.content = "world!"
    
    mock_stream = MockAsyncIterator([chunk1, chunk2])
    mock_complete = AsyncMock(return_value=mock_stream)
    
    with patch("app.api.v1.endpoints.public_chat.check_and_increment_demo_limits", mock_rate_limit), \
         patch("app.api.v1.endpoints.public_chat.complete_demo_stream", mock_complete):
         
        response = await client.post(
            "/api/v1/public/chat",
            json={"message": "Hi", "session_id": session_id}
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        # Read the stream lines
        lines = [line async for line in response.aiter_lines()]
        
        # Parse data lines
        data_lines = [line[6:] for line in lines if line.startswith("data: ")]
        parsed = [json.loads(d) for d in data_lines]
        
        assert len(parsed) == 3
        assert parsed[0] == {"type": "token", "content": "Hello "}
        assert parsed[1] == {"type": "token", "content": "world!"}
        assert parsed[2] == {"type": "done", "message_count": 1}

@pytest.mark.asyncio
async def test_public_chat_invalid_requests(client: AsyncClient):
    # Test missing payload
    response = await client.post("/api/v1/public/chat", json={})
    assert response.status_code == 400
    
    # Test invalid session_id (not uuid4)
    response = await client.post(
        "/api/v1/public/chat",
        json={"message": "Hi", "session_id": "not-a-uuid"}
    )
    assert response.status_code == 400
    
    # Test invalid message (empty/whitespace)
    response = await client.post(
        "/api/v1/public/chat",
        json={"message": "   ", "session_id": str(uuid.uuid4())}
    )
    assert response.status_code == 400
    
    # Test too long message
    long_msg = "a" * 501
    response = await client.post(
        "/api/v1/public/chat",
        json={"message": long_msg, "session_id": str(uuid.uuid4())}
    )
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_public_chat_quota_exceeded(client: AsyncClient):
    session_id = str(uuid.uuid4())
    mock_rate_limit = AsyncMock(return_value=(False, 5))
    
    with patch("app.api.v1.endpoints.public_chat.check_and_increment_demo_limits", mock_rate_limit):
        response = await client.post(
            "/api/v1/public/chat",
            json={"message": "Hi", "session_id": session_id}
        )
        assert response.status_code == 429
        data = response.json()
        assert data["error"]["code"] == "DEMO_QUOTA_EXCEEDED"
        assert data["error"]["message_count"] == 5

@pytest.mark.asyncio
async def test_public_chat_llm_unavailable(client: AsyncClient):
    session_id = str(uuid.uuid4())
    mock_rate_limit = AsyncMock(return_value=(True, 1))
    
    # Mock LLM failure
    mock_complete = AsyncMock(side_effect=LLMUnavailableError("Service down"))
    
    with patch("app.api.v1.endpoints.public_chat.check_and_increment_demo_limits", mock_rate_limit), \
         patch("app.api.v1.endpoints.public_chat.complete_demo_stream", mock_complete):
         
        response = await client.post(
            "/api/v1/public/chat",
            json={"message": "Hi", "session_id": session_id}
        )
        assert response.status_code == 503
        data = response.json()
        assert data["error"]["code"] == "SERVICE_UNAVAILABLE"
