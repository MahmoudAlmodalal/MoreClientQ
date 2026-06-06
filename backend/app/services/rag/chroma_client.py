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

    def upsert_document_chunks(self, tenant_id: str, document_id: str, chunks: list, filename: str, file_type: str) -> int:
        """
        Upsert document chunks into tenant-isolated ChromaDB collection.
        Returns the number of chunks upserted.
        """
        collection_name = f"tenant_{tenant_id}"
        collection = self.client.get_or_create_collection(name=collection_name)
        
        ids = []
        documents = []
        metadatas = []
        
        for idx, chunk in enumerate(chunks):
            chunk_id = f"{document_id}_{idx}"
            ids.append(chunk_id)
            documents.append(chunk.text)
            metadatas.append({
                "tenant_id": str(tenant_id),
                "document_id": str(document_id),
                "filename": filename,
                "file_type": file_type,
                "chunk_index": idx
            })
            
        if ids:
            collection.upsert(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
        return len(ids)

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

