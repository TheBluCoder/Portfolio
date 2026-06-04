from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from src.config.settings import AZURE_TABLE_CONNECTION_STRING
from src.models.schemas import Poem, PoemComment

try:
    from azure.data.tables import TableServiceClient, UpdateMode
except ImportError:  # pragma: no cover
    TableServiceClient = None
    UpdateMode = None


class GalleryService:
    _memory_poems: dict[str, dict[str, Any]] = {}
    _memory_comments: dict[str, dict[str, Any]] = {}
    _memory_likes: set[str] = set()

    def __init__(self, connection_string: str | None = AZURE_TABLE_CONNECTION_STRING) -> None:
        self.connection_string = connection_string
        self._poems = None
        self._comments = None
        self._likes = None

    def list_poems(self) -> list[Poem]:
        if self._use_memory:
            poems = list(self._memory_poems.values())
            return [self._with_approved_comments(poem.copy()) for poem in poems]

        poems = list(self._poems_table.query_entities("PartitionKey eq 'poem'"))
        return [self._with_approved_comments(dict(poem)) for poem in poems]

    def create_poem(
        self,
        title: str,
        body: str,
        excerpt: str | None,
        tags: list[str],
    ) -> Poem:
        now = self._now()
        poem = {
            "PartitionKey": "poem",
            "RowKey": uuid4().hex,
            "title": title,
            "body": body,
            "excerpt": excerpt or body[:160],
            "tags": ",".join(tags),
            "likes": 0,
            "created_at": now,
        }

        if self._use_memory:
            self._memory_poems[poem["RowKey"]] = poem
        else:
            self._poems_table.upsert_entity(poem, mode=UpdateMode.MERGE)

        return self._serialize_poem(poem)

    def like_poem(self, poem_id: str, visitor_key: str) -> Poem:
        like_id = f"{poem_id}:{visitor_key}"
        if self._use_memory:
            poem = self._memory_poems[poem_id]
            if like_id not in self._memory_likes:
                self._memory_likes.add(like_id)
                poem["likes"] = poem.get("likes", 0) + 1
            return self._serialize_poem(poem)

        like = {"PartitionKey": "like", "RowKey": like_id, "poem_id": poem_id}
        try:
            self._likes_table.create_entity(like)
            poem = self._poems_table.get_entity("poem", poem_id)
            poem["likes"] = poem.get("likes", 0) + 1
            self._poems_table.upsert_entity(poem, mode=UpdateMode.MERGE)
        except Exception:
            poem = self._poems_table.get_entity("poem", poem_id)
        return self._serialize_poem(dict(poem))

    def add_comment(
        self,
        poem_id: str,
        author: str,
        body: str,
        visitor_key: str,
    ) -> PoemComment:
        comment = {
            "PartitionKey": "comment",
            "RowKey": uuid4().hex,
            "poem_id": poem_id,
            "author": author,
            "body": body,
            "visitor_key": visitor_key,
            "approved": False,
            "created_at": self._now(),
        }

        if self._use_memory:
            self._memory_comments[comment["RowKey"]] = comment
        else:
            self._comments_table.upsert_entity(comment, mode=UpdateMode.MERGE)

        return self._serialize_comment(comment)

    def list_pending_comments(self) -> list[PoemComment]:
        if self._use_memory:
            return [
                self._serialize_comment(comment)
                for comment in self._memory_comments.values()
                if not comment.get("approved")
            ]

        comments = self._comments_table.query_entities(
            "PartitionKey eq 'comment' and approved eq false"
        )
        return [self._serialize_comment(dict(comment)) for comment in comments]

    def moderate_comment(self, comment_id: str, approved: bool) -> PoemComment:
        if self._use_memory:
            comment = self._memory_comments[comment_id]
            comment["approved"] = approved
            return self._serialize_comment(comment)

        comment = self._comments_table.get_entity("comment", comment_id)
        comment["approved"] = approved
        self._comments_table.upsert_entity(comment, mode=UpdateMode.MERGE)
        return self._serialize_comment(dict(comment))

    def _with_approved_comments(self, poem: dict[str, Any]) -> Poem:
        poem_id = poem["RowKey"]
        if self._use_memory:
            comments = [
                self._serialize_comment(comment)
                for comment in self._memory_comments.values()
                if comment.get("poem_id") == poem_id and comment.get("approved")
            ]
        else:
            comments = self._comments_table.query_entities(
                f"PartitionKey eq 'comment' and poem_id eq '{poem_id}' and approved eq true"
            )
            comments = [self._serialize_comment(dict(comment)) for comment in comments]

        serialized = self._serialize_poem(poem)
        return serialized.model_copy(update={"comments": comments})

    def _serialize_poem(self, poem: dict[str, Any]) -> Poem:
        return Poem(
            id=poem["RowKey"],
            title=poem["title"],
            body=poem["body"],
            excerpt=poem.get("excerpt"),
            tags=[tag for tag in poem.get("tags", "").split(",") if tag],
            likes=poem.get("likes", 0),
            created_at=poem.get("created_at"),
        )

    def _serialize_comment(self, comment: dict[str, Any]) -> PoemComment:
        return PoemComment(
            id=comment["RowKey"],
            poem_id=comment["poem_id"],
            author=comment["author"],
            body=comment["body"],
            approved=comment.get("approved", False),
            created_at=comment.get("created_at"),
        )

    @property
    def _use_memory(self) -> bool:
        return not self.connection_string or not TableServiceClient

    @property
    def _poems_table(self) -> Any:
        self._ensure_tables()
        return self._poems

    @property
    def _comments_table(self) -> Any:
        self._ensure_tables()
        return self._comments

    @property
    def _likes_table(self) -> Any:
        self._ensure_tables()
        return self._likes

    def _ensure_tables(self) -> None:
        if self._poems:
            return
        service = TableServiceClient.from_connection_string(self.connection_string)
        for table_name in ("GalleryPoems", "GalleryComments", "GalleryLikes"):
            service.create_table_if_not_exists(table_name)
        self._poems = service.get_table_client("GalleryPoems")
        self._comments = service.get_table_client("GalleryComments")
        self._likes = service.get_table_client("GalleryLikes")

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()
