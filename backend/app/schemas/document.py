from pydantic import BaseModel, ConfigDict, HttpUrl
from uuid import UUID
from datetime import datetime
from typing import Literal

DocumentFileType = Literal["pdf", "docx", "txt", "url"]
DocumentStatus = Literal["pending", "processing", "ready", "failed"]

class DocumentResponse(BaseModel):
    id: UUID
    assistant_id: UUID
    filename: str
    file_type: DocumentFileType
    status: DocumentStatus
    chunk_count: int | None
    error_message: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DocumentStatusResponse(BaseModel):
    id: UUID
    status: DocumentStatus
    chunk_count: int | None
    error_message: str | None

    model_config = ConfigDict(from_attributes=True)

class URLIngestRequest(BaseModel):
    url: HttpUrl
    assistant_id: UUID
