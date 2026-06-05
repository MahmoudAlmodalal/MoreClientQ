import redis.asyncio as redis
from src.config import settings

# Initialize async Redis client
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

def tenant_key(tenant_id: str | object, key: str) -> str:
    """Namespace-isolate keys per tenant to enforce isolation rules."""
    return f"{str(tenant_id)}:{key}"

async def incr_usage(tenant_id: str | object, metric: str, amount: int = 1) -> int:
    """Increment a metric count atomically for a tenant."""
    key = tenant_key(tenant_id, f"usage:{metric}")
    val = await redis_client.incrby(key, amount)
    return int(val)

async def get_usage(tenant_id: str | object, metric: str) -> int:
    """Get the current value of a tenant's usage metric."""
    key = tenant_key(tenant_id, f"usage:{metric}")
    val = await redis_client.get(key)
    return int(val) if val else 0
