import logging
import time
import redis.asyncio as aioredis
from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize Redis Connection Pool
pool = aioredis.ConnectionPool.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    max_connections=100,
    socket_connect_timeout=1,
    socket_timeout=1,
)

redis_client = aioredis.Redis(connection_pool=pool)

class RedisCache:
    """Async Redis caching helper client."""
    def __init__(self, client: aioredis.Redis = redis_client):
        self.client = client

    async def get(self, key: str) -> str | None:
        try:
            return await self.client.get(key)
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None

    async def set(self, key: str, value: str, expire: int | None = None) -> bool:
        try:
            return await self.client.set(key, value, ex=expire)
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            return False

    async def exists(self, key: str) -> bool:
        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            return False

    async def incr(self, key: str, expire: int | None = None) -> int | None:
        try:
            value = await self.client.incr(key)
            if value == 1 and expire is not None:
                await self.client.expire(key, expire)
            return int(value)
        except Exception as e:
            logger.error(f"Redis incr error for key {key}: {e}")
            return None

    async def incrby(self, key: str, amount: int, expire: int | None = None) -> int | None:
        try:
            value = await self.client.incrby(key, amount)
            if expire is not None:
                await self.client.expire(key, expire)
            return int(value)
        except Exception as e:
            logger.error(f"Redis incrby error for key {key}: {e}")
            return None

    async def ping(self) -> tuple[bool, float, str | None]:
        start_time = time.perf_counter()
        try:
            await self.client.ping()
            latency = (time.perf_counter() - start_time) * 1000
            return True, round(latency, 2), None
        except Exception as e:
            latency = (time.perf_counter() - start_time) * 1000
            return False, round(latency, 2), str(e)

redis_cache = RedisCache()
