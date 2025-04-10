from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime, timezone

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Content(BaseModel):
    id: str
    text: str
    dateCreated: datetime = Field(default_factory=utc_now)
    dateModified: datetime = Field(default_factory=utc_now)

class DocumentRequest(BaseModel):
    """@deprecated: Use /indexes/{index_name}/upsert with Content schema instead"""
    index_name: str
    content: Content

class Message(BaseModel):
    type: Literal["human", "ai"]
    content: str

class ChatRequest(BaseModel):
    context: list[Message] = None


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime

class DeleteIndexResponse(BaseModel):
    message: str
    deleted_index: str
    timestamp: datetime 