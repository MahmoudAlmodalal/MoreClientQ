import time
import httpx
import chromadb
from app.core.config import settings

class ChromaClient:
    def __init__(self):
        self.host = settings.CHROMADB_HOST
        self.port = settings.CHROMADB_PORT
        self.base_url = f"http://{self.host}:{self.port}"
        self._client = None

    @property
    def client(self) -> chromadb.HttpClient:
        if self._client is None:
            self._client = chromadb.HttpClient(host=self.host, port=self.port)
        return self._client

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

    def delete_document_vectors(self, tenant_id: str, document_id: str) -> None:
        """
        Delete all vector chunks belonging to the specified document.
        Uses the tenant-isolated ChromaDB collection name: tenant_{tenant_id}.
        """
        collection_name = f"tenant_{tenant_id}"
        try:
            collection = self.client.get_or_create_collection(name=collection_name)
            collection.delete(where={"document_id": str(document_id)})
        except Exception as e:
            # If the collection doesn't exist, it might raise an error or just return.
            # We wrap it to be safe.
            pass

chroma_client = ChromaClient()

