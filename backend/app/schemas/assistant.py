from typing import Annotated

from pydantic import BaseModel, Field, ConfigDict, StringConstraints
from uuid import UUID
from datetime import datetime

class AssistantCreate(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
    system_prompt: str = Field(default="")
    model: str = Field(default="gpt-4o-mini", max_length=100)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1024, ge=1, le=8192)

class AssistantUpdate(BaseModel):
    name: Annotated[str | None, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)] = None
    system_prompt: str | None = None
    model: str | None = Field(None, max_length=100)
    temperature: float | None = Field(None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(None, ge=1, le=8192)
    is_active: bool | None = None

class AssistantResponse(BaseModel):
    id: UUID
    name: str
    system_prompt: str
    model: str
    temperature: float
    max_tokens: int
    is_active: bool
    widget_config: dict
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
