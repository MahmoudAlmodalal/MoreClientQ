import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_check_endpoint(client: AsyncClient):
    # Test versioned endpoint
    response = await client.get("/api/v1/health")
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "services" in data
    assert "database" in data["services"]
    assert "redis" in data["services"]
    assert "chromadb" in data["services"]

    # Test root endpoint
    response_root = await client.get("/health")
    assert response_root.status_code == response.status_code
    assert response_root.json()["status"] == data["status"]
