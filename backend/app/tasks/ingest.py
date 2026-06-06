import logging
import io
import asyncio
import httpx
import fitz  # PyMuPDF
import docx2txt
from html.parser import HTMLParser
from uuid import UUID
from sqlalchemy.future import select
from celery.exceptions import MaxRetriesExceededError

from app.tasks.celery_app import celery_app
from app.db.session import SessionLocal, enable_rls_bypass
from app.models.document import Document
from app.services.storage import storage_service
from app.services.rag.chroma_client import chroma_client
from app.services.rag.chunker import chunk_text

logger = logging.getLogger(__name__)

class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.result = []
        self.in_script = False
        self.in_style = False

    def handle_starttag(self, tag, attrs):
        if tag.lower() in ("script", "style"):
            if tag.lower() == "script":
                self.in_script = True
            if tag.lower() == "style":
                self.in_style = True

    def handle_endtag(self, tag):
        if tag.lower() == "script":
            self.in_script = False
        if tag.lower() == "style":
            self.in_style = False

    def handle_data(self, data):
        if not self.in_script and not self.in_style:
            self.result.append(data)

    def get_text(self):
        return " ".join("".join(self.result).split())

def extract_text_from_html(html_content: str) -> str:
    parser = HTMLTextExtractor()
    parser.feed(html_content)
    return parser.get_text()

async def async_ingest_document(self, document_id: str):
    logger.info(f"Starting ingestion for document {document_id}")
    
    async with SessionLocal() as session:
        await enable_rls_bypass(session)
        doc_uuid = UUID(document_id)
        
        # 1. Fetch document
        result = await session.execute(
            select(Document).where(Document.id == doc_uuid)
        )
        doc = result.scalar_one_or_none()
        if not doc:
            logger.error(f"Document {document_id} not found in database.")
            return

        # Initialize retry tracking in metadata
        if not isinstance(doc.doc_metadata, dict):
            doc.doc_metadata = {}
        
        current_attempt = doc.doc_metadata.get("retry_count", 0) + 1
        doc.doc_metadata["retry_count"] = current_attempt

        # 2. Update status to processing
        doc.status = "processing"
        await session.commit()
        await session.refresh(doc)

        try:
            text_content = ""
            if doc.file_type == "url":
                # Ingest URL
                url = doc.filename
                logger.info(f"Fetching content from URL: {url} (Attempt {current_attempt})")
                async with httpx.AsyncClient(timeout=15.0) as client:
                    response = await client.get(url, follow_redirects=True)
                    response.raise_for_status()
                    html = response.text
                    text_content = extract_text_from_html(html)
            else:
                # Download and extract from file
                logger.info(f"Downloading file from storage key: {doc.storage_key} (Attempt {current_attempt})")
                file_bytes = await asyncio.to_thread(storage_service.get_file, doc.storage_key)
                
                if doc.file_type == "pdf":
                    doc_fitz = fitz.open(stream=file_bytes, filetype="pdf")
                    pages_text = []
                    for page in doc_fitz:
                        pages_text.append(page.get_text())
                    text_content = "\n".join(pages_text)
                elif doc.file_type == "docx":
                    text_content = docx2txt.process(io.BytesIO(file_bytes))
                elif doc.file_type == "txt":
                    text_content = file_bytes.decode("utf-8", errors="ignore")
                else:
                    raise ValueError(f"Unsupported file type: {doc.file_type}")

            if not text_content.strip():
                raise ValueError("No text content could be extracted from the document.")

            # 3. Chunk text
            logger.info(f"Chunking document {document_id}")
            chunks = chunk_text(text_content)
            
            # 4. Embed and index in ChromaDB
            logger.info(f"Indexing chunks in ChromaDB for document {document_id}")
            # Run the Chroma client call in a thread pool since chromadb client is synchronous
            chunk_count = await asyncio.to_thread(
                chroma_client.upsert_document_chunks,
                tenant_id=str(doc.tenant_id),
                document_id=str(doc.id),
                chunks=chunks,
                filename=doc.filename,
                file_type=doc.file_type
            )

            # 5. Success
            doc.status = "ready"
            doc.chunk_count = chunk_count
            doc.error_message = None
            await session.commit()
            logger.info(f"Ingestion successful for document {document_id} with {chunk_count} chunks.")

        except Exception as e:
            logger.exception(f"Ingestion failed for document {document_id} on attempt {current_attempt}")
            doc.error_message = str(e)
            
            # Structured logging of ingestion failure (T020)
            import datetime
            log_payload = {
                "event": "ingestion_failure",
                "document_id": document_id,
                "tenant_id": str(doc.tenant_id),
                "assistant_id": str(doc.assistant_id),
                "filename_or_url": doc.filename,
                "attempt": current_attempt,
                "error": str(e),
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
            logger.error(f"STRUCTURED_LOG: {log_payload}")

            # Check if we should retry
            if current_attempt <= 3:
                await session.commit()
                # Trigger Celery retry (self.retry will raise a retry exception)
                try:
                    self.retry(exc=e, countdown=30)
                except Exception as retry_exc:
                    # Let Celery handle its own retry exceptions
                    raise retry_exc
            else:
                doc.status = "failed"
                doc.error_message = f"Failed after {current_attempt} attempts. Error: {str(e)}"
                await session.commit()
                logger.error(f"Max retries exhausted for document {document_id}.")

@celery_app.task(bind=True, max_retries=3)
def ingest_document(self, document_id: str):
    """Celery task entry point."""
    asyncio.run(async_ingest_document(self, document_id))
