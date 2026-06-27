from pydantic import BaseModel, Field, model_validator
from typing import Literal
from datetime import datetime, timezone

CHAT_USER_MESSAGE_MAX_LENGTH = 1000

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Content(BaseModel):
    id: str
    text: str
    dateCreated: datetime = Field(default_factory=utc_now)
    dateModified: datetime = Field(default_factory=utc_now)

class Message(BaseModel):
    type: Literal["human", "ai"]
    content: str

    @model_validator(mode="after")
    def validate_human_message_length(self) -> "Message":
        if self.type == "human" and len(self.content) > CHAT_USER_MESSAGE_MAX_LENGTH:
            raise ValueError(
                f"Human message content must be at most {CHAT_USER_MESSAGE_MAX_LENGTH} characters"
            )
        return self

class ChatRequest(BaseModel):
    context: list[Message] | None = None


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime

class PoemCreate(BaseModel):
    title: str
    body: str
    excerpt: str | None = None
    tags: list[str] = Field(default_factory=list)

class ProjectContextUpsert(BaseModel):
    context_id: str = Field(default="manual-context", min_length=1)
    text: str = Field(min_length=1)
    title: str | None = None
    owner: str | None = None

class CommentCreate(BaseModel):
    author: str
    body: str

class CommentModeration(BaseModel):
    approved: bool

class Comment(BaseModel):
    id: str
    poem_id: str
    author: str
    body: str
    approved: bool = False
    created_at: str | None = None

class Like(BaseModel):
    id: str
    poem_id: str
    likes: int
    liked: bool = True
    created_at: str | None = None

class PoemUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    excerpt: str | None = None
    tags: list[str] | None = None

class Poem(BaseModel):
    id: str
    title: str
    body: str
    excerpt: str | None = None
    tags: list[str] = Field(default_factory=list)
    likes: int = 0
    created_at: str | None = None
    comments: list[Comment] = Field(default_factory=list)
