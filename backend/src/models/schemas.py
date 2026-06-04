from pydantic import BaseModel, Field
from typing import Literal
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

class PoemCreate(BaseModel):
    title: str
    body: str
    excerpt: str | None = None
    tags: list[str] = Field(default_factory=list)

class CommentCreate(BaseModel):
    author: str
    body: str

class CommentModeration(BaseModel):
    approved: bool

class PoemComment(BaseModel):
    id: str
    poem_id: str
    author: str
    body: str
    approved: bool = False
    created_at: str | None = None

class Poem(BaseModel):
    id: str
    title: str
    body: str
    excerpt: str | None = None
    tags: list[str] = Field(default_factory=list)
    likes: int = 0
    created_at: str | None = None
    comments: list[PoemComment] = Field(default_factory=list)
