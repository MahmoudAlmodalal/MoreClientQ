from typing import Literal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict

class SourceReference(BaseModel):
    document_id: UUID
    chunk_text: str
    score: float

    model_config = ConfigDict(from_attributes=True)

class ChatRequest(BaseModel):
    assistant_id: UUID
    conversation_id: UUID | None = None
    message: str = Field(..., max_length=4000)

class ChatResponse(BaseModel):
    conversation_id: UUID
    message_id: UUID
    role: str = "assistant"
    content: str
    tokens_used: int = 0
    sources: list[SourceReference] = Field(default_factory=list)
    model_used: str | None = None

    model_config = ConfigDict(from_attributes=True)

class WSIncomingMessage(BaseModel):
    type: Literal["message", "ping"]
    conversation_id: UUID | None = None
    content: str | None = None

class WSTokenEvent(BaseModel):
    type: Literal["token"] = "token"
    delta: str

class WSDoneEvent(BaseModel):
    type: Literal["done"] = "done"
    conversation_id: UUID
    message_id: UUID
    tokens_used: int
    model_used: str | None = None
    sources: list[SourceReference] = Field(default_factory=list)

class WSErrorEvent(BaseModel):
    type: Literal["error"] = "error"
    code: str
    detail: str

class WSHandoffEvent(BaseModel):
    type: Literal["handoff"] = "handoff"
    conversation_id: UUID
    detail: str
