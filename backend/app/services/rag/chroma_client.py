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
                res = await client.get(f"{self.base_url}/api/v1/heartbeat", timeout=2.0)
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
        collection = self.client.get_or_create_collection(name=collection_name)
        collection.delete(where={"document_id": str(document_id)})

    async def retrieve(self, tenant_id: str, query_text: str, top_k: int) -> list:
        """
        Retrieve top_k most similar document chunks for a query from the tenant-isolated collection.
        Returns a list of SourceReference schema objects.
        """
        from app.schemas.chat import SourceReference
        import asyncio
        from uuid import UUID

        collection_name = f"tenant_{tenant_id}"

        def _query():
            collection = self.client.get_or_create_collection(name=collection_name)
            return collection.query(
                query_texts=[query_text],
                n_results=top_k
            )

        results = await asyncio.to_thread(_query)

        source_references = []
        if not results or "documents" not in results or not results["documents"]:
            return source_references

        docs = results["documents"][0]
        metas = results["metadatas"][0] if "metadatas" in results and results["metadatas"] else []
        distances = results["distances"][0] if "distances" in results and results["distances"] else []

        for i in range(len(docs)):
            doc_id_str = metas[i].get("document_id") if i < len(metas) and metas[i] else None
            if not doc_id_str:
                continue
            try:
                document_id = UUID(doc_id_str)
            except ValueError:
                continue

            dist = distances[i] if i < len(distances) and distances[i] is not None else 0.0
            # Convert distance to similarity score
            score = max(0.0, 1.0 - float(dist))

            source_references.append(
                SourceReference(
                    document_id=document_id,
                    chunk_text=docs[i],
                    score=score
                )
            )

        return source_references

chroma_client = ChromaClient()


