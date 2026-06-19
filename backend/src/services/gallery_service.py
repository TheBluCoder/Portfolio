from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Mapping, TypedDict, cast
from uuid import uuid4

from src.config.settings import AZURE_TABLE_CONNECTION_STRING
from src.models.schemas import Comment, Like, Poem

if TYPE_CHECKING:
    from azure.data.tables import TableClient
else:
    TableClient = Any
    TableServiceClient = Any

try:
    from azure.data.tables import TableServiceClient as AzureTableServiceClient
    from azure.data.tables import UpdateMode
except ImportError:  # pragma: no cover
    AzureTableServiceClient = None
    UpdateMode = None


class PoemEntity(TypedDict):
    PartitionKey: str
    RowKey: str
    title: str
    body: str
    excerpt: str | None
    tags: str
    likes: int
    created_at: str


class CommentEntity(TypedDict):
    PartitionKey: str
    RowKey: str
    poem_id: str
    author: str
    body: str
    visitor_key: str
    approved: bool
    created_at: str


class LikeEntity(TypedDict):
    PartitionKey: str
    RowKey: str
    poem_id: str
    created_at: str


class GalleryService:
    _memory_poems: dict[str, PoemEntity] = {}
    _memory_comments: dict[str, CommentEntity] = {}
    _memory_likes: set[str] = set()

    def __init__(self, connection_string: str | None = AZURE_TABLE_CONNECTION_STRING) -> None:
        self.connection_string = connection_string
        self._poems: TableClient | None = None
        self._comments: TableClient | None = None
        self._likes: TableClient | None = None

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
        poem: PoemEntity = {
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
            self._poems_table.upsert_entity(poem, mode=self._merge_mode)

        return self._serialize_poem(poem)

    def like_poem(self, poem_id: str, visitor_key: str) -> Like:
        like_id = f"{poem_id}:{visitor_key}"
        liked = False
        created_at = self._now()
        if self._use_memory:
            poem = self._memory_poems[poem_id]
            if like_id not in self._memory_likes:
                self._memory_likes.add(like_id)
                poem["likes"] = poem.get("likes", 0) + 1
                liked = True
            return self._serialize_like(like_id, poem_id, poem.get("likes", 0), liked, created_at)

        like: LikeEntity = {
            "PartitionKey": "like",
            "RowKey": like_id,
            "poem_id": poem_id,
            "created_at": created_at,
        }
        try:
            self._likes_table.create_entity(like)
            poem = cast(dict[str, Any], self._poems_table.get_entity("poem", poem_id))
            poem["likes"] = poem.get("likes", 0) + 1
            self._poems_table.upsert_entity(poem, mode=self._merge_mode)
            liked = True
        except Exception:
            poem = cast(dict[str, Any], self._poems_table.get_entity("poem", poem_id))
        return self._serialize_like(like_id, poem_id, poem.get("likes", 0), liked, created_at)

    def add_comment(
        self,
        poem_id: str,
        author: str,
        body: str,
        visitor_key: str,
    ) -> Comment:
        comment: CommentEntity = {
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
            self._comments_table.upsert_entity(comment, mode=self._merge_mode)

        return self._serialize_comment(comment)

    def get_poem(self, poem_id: str) -> Poem:
        if self._use_memory:
            poem = self._memory_poems.get(poem_id)
            if not poem:
                raise KeyError(f"Poem {poem_id} not found")
            return self._with_approved_comments(poem.copy())

        from azure.core.exceptions import ResourceNotFoundError
        try:
            poem = self._poems_table.get_entity("poem", poem_id)
        except ResourceNotFoundError:
            raise KeyError(f"Poem {poem_id} not found")
        return self._with_approved_comments(dict(poem))

    def update_poem(
        self,
        poem_id: str,
        title: str | None,
        body: str | None,
        excerpt: str | None,
        tags: list[str] | None,
    ) -> Poem:
        if self._use_memory:
            poem = self._memory_poems.get(poem_id)
            if not poem:
                raise KeyError(f"Poem {poem_id} not found")
            if title is not None:
                poem["title"] = title
            if body is not None:
                poem["body"] = body
            if excerpt is not None:
                poem["excerpt"] = excerpt
            if tags is not None:
                poem["tags"] = ",".join(tags)
            return self._serialize_poem(poem)

        from typing import cast as t_cast
        poem = t_cast(dict, self._poems_table.get_entity("poem", poem_id))
        if title is not None:
            poem["title"] = title
        if body is not None:
            poem["body"] = body
            if excerpt is None:
                poem["excerpt"] = body[:160]
        if excerpt is not None:
            poem["excerpt"] = excerpt
        if tags is not None:
            poem["tags"] = ",".join(tags)
        self._poems_table.upsert_entity(poem, mode=self._merge_mode)
        return self._serialize_poem(poem)

    def delete_poem(self, poem_id: str) -> None:
        if self._use_memory:
            self._memory_poems.pop(poem_id, None)
            # remove associated comments + likes
            self._memory_comments = {
                cid: c for cid, c in self._memory_comments.items()
                if c.get("poem_id") != poem_id
            }
            self._memory_likes = {
                like for like in self._memory_likes
                if not like.startswith(poem_id + ":")
            }
            return

        self._poems_table.delete_entity("poem", poem_id)

    def list_pending_comments(self) -> list[Comment]:
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

    def moderate_comment(self, comment_id: str, approved: bool) -> Comment:
        if self._use_memory:
            comment = self._memory_comments[comment_id]
            comment["approved"] = approved
            return self._serialize_comment(comment)

        comment = cast(dict[str, Any], self._comments_table.get_entity("comment", comment_id))
        comment["approved"] = approved
        self._comments_table.upsert_entity(comment, mode=self._merge_mode)
        return self._serialize_comment(dict(comment))

    def _with_approved_comments(self, poem: Mapping[str, Any]) -> Poem:
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

    def _serialize_poem(self, poem: Mapping[str, Any]) -> Poem:
        return Poem(
            id=poem["RowKey"],
            title=poem["title"],
            body=poem["body"],
            excerpt=poem.get("excerpt"),
            tags=[tag for tag in poem.get("tags", "").split(",") if tag],
            likes=poem.get("likes", 0),
            created_at=poem.get("created_at"),
        )

    def _serialize_comment(self, comment: Mapping[str, Any]) -> Comment:
        return Comment(
            id=comment["RowKey"],
            poem_id=comment["poem_id"],
            author=comment["author"],
            body=comment["body"],
            approved=comment.get("approved", False),
            created_at=comment.get("created_at"),
        )

    def _serialize_like(
        self,
        like_id: str,
        poem_id: str,
        likes: int,
        liked: bool,
        created_at: str | None,
    ) -> Like:
        return Like(
            id=like_id,
            poem_id=poem_id,
            likes=likes,
            liked=liked,
            created_at=created_at,
        )

    @property
    def _use_memory(self) -> bool:
        return not self.connection_string or AzureTableServiceClient is None

    @property
    def _poems_table(self) -> TableClient:
        self._ensure_tables()
        if self._poems is None:
            raise RuntimeError("Poems table is not initialized.")
        return self._poems

    @property
    def _comments_table(self) -> TableClient:
        self._ensure_tables()
        if self._comments is None:
            raise RuntimeError("Comments table is not initialized.")
        return self._comments

    @property
    def _likes_table(self) -> TableClient:
        self._ensure_tables()
        if self._likes is None:
            raise RuntimeError("Likes table is not initialized.")
        return self._likes

    @property
    def _merge_mode(self) -> Any:
        if UpdateMode is None:
            raise RuntimeError("Azure Table Storage dependencies are not available.")
        return UpdateMode.MERGE

    def _ensure_tables(self) -> None:
        if self._poems:
            return
        if AzureTableServiceClient is None:
            raise RuntimeError("Azure Table Storage dependencies are not available.")
        if self.connection_string is None:
            raise RuntimeError("Azure Table connection string is not configured.")

        service = AzureTableServiceClient.from_connection_string(self.connection_string)
        for table_name in ("GalleryPoems", "GalleryComments", "GalleryLikes"):
            service.create_table_if_not_exists(table_name)
        self._poems = service.get_table_client("GalleryPoems")
        self._comments = service.get_table_client("GalleryComments")
        self._likes = service.get_table_client("GalleryLikes")

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()
