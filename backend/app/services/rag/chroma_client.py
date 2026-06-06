import time
import httpx
from app.core.config import settings

class ChromaClient:
    def __init__(self):
        self.host = settings.CHROMADB_HOST
        self.port = settings.CHROMADB_PORT
        self.base_url = f"http://{self.host}:{self.port}"

    async def ping(self) -> tuple[bool, float, str | None]:
        start_time = time.perf_counter()
        try:
            async with httpx.AsyncClient() as client:
                res = await client.get(f"{self.base_url}/api/v2/heartbeat", timeout=2.0)
                latency = (time.perf_counter() - start_time) * 1000
                if res.status_code == 200:
                    return True, round(latency, 2), None
                else:
                    return False, round(latency, 2), f"Unexpected status: {res.status_code}"
        except Exception as e:
            latency = (time.perf_counter() - start_time) * 1000
            return False, round(latency, 2), str(e)

chroma_client = ChromaClient()
