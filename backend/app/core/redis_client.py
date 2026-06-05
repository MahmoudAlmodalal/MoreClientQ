import time
import redis.asyncio as aioredis
from app.core.config import settings

class RedisClient:
    def __init__(self):
        self.client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

    async def ping(self) -> tuple[bool, float, str | None]:
        start_time = time.perf_counter()
        try:
            await self.client.ping()
            latency = (time.perf_counter() - start_time) * 1000
            return True, round(latency, 2), None
        except Exception as e:
            latency = (time.perf_counter() - start_time) * 1000
            return False, round(latency, 2), str(e)

redis_client = RedisClient()
