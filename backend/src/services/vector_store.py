from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models
from src.config import settings

# Async Qdrant client connected to QDRANT_URL
qdrant_client = AsyncQdrantClient(url=settings.QDRANT_URL)

def get_collection_name(region: str) -> str:
    """Returns collection name according to tenant region for isolation."""
    if str(region).strip().upper() == "GCC":
        return "moreclient_vectors_gcc"
    return "moreclient_vectors_global"

async def ensure_collection(region: str) -> None:
    """Ensures a Qdrant collection exists for the region with 1536 dimensions & Cosine metric."""
    collection_name = get_collection_name(region)
    exists = await qdrant_client.collection_exists(collection_name)
    if not exists:
        await qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=1536,
                distance=models.Distance.COSINE
            )
        )

def tenant_filter(tenant_id: str | object) -> models.Filter:
    """Builds a Qdrant search/retrieval filter payload to isolate tenant vector queries."""
    return models.Filter(
        must=[
            models.FieldCondition(
                key="tenant_id",
                match=models.MatchValue(value=str(tenant_id))
            )
        ]
    )
