"""Reading list service — dual-mode CRUD backed by Azure Table Storage or in-memory state."""
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from typing_extensions import TypedDict

from src.config.log_config import setup_logging
from src.config.settings import AZURE_TABLE_CONNECTION_STRING

if TYPE_CHECKING:
    from azure.data.tables import TableClient

logger = setup_logging(filename=__file__)


class CurrentBook(TypedDict):
    title: str
    author: str
    cover: str | None
    thoughts: str
    progress: int
    since: str


class RecentBook(TypedDict):
    id: str
    title: str
    author: str
    finished_at: str


_DEFAULT_CURRENT: CurrentBook = {
    "title": "The Pragmatic Programmer",
    "author": "David Thomas & Andrew Hunt",
    "cover": None,
    "thoughts": (
        "A book about becoming a better programmer — not through tools, "
        "but through habits of mind. Working through it slowly."
    ),
    "progress": 40,
    "since": "2025-05",
}

# Module-level in-memory state used when Azure Tables are unavailable.
_current: CurrentBook = {**_DEFAULT_CURRENT}
_recent: list[RecentBook] = []


def _entity_to_current(entity: dict[str, Any]) -> CurrentBook:
    """Convert an Azure Table entity into the current-book response shape."""
    return {
        "title": str(entity.get("title", "")),
        "author": str(entity.get("author", "")),
        "cover": entity.get("cover") or None,
        "thoughts": str(entity.get("thoughts", "")),
        "progress": int(entity.get("progress", 0)),
        "since": str(entity.get("since", "")),
    }


def _entity_to_recent(entity: dict[str, Any]) -> RecentBook:
    """Convert an Azure Table entity into a recently finished book."""
    return {
        "id": str(entity["RowKey"]),
        "title": str(entity.get("title", "")),
        "author": str(entity.get("author", "")),
        "finished_at": str(entity.get("finished_at", "")),
    }


class ReadingService:
    """Manages the reading list with Azure Table Storage or in-memory fallback.

    Table layout:
        PartitionKey="current", RowKey="book"  → CurrentBook fields
        PartitionKey="recent",  RowKey=<uuid>  → RecentBook fields
    """

    def __init__(self) -> None:
        self._use_azure: bool = bool(AZURE_TABLE_CONNECTION_STRING)
        self._table: TableClient  # initialised below when Azure is available
        if self._use_azure:
            try:
                from azure.data.tables import TableServiceClient

                service = TableServiceClient.from_connection_string(AZURE_TABLE_CONNECTION_STRING)
                self._table = service.get_table_client("ReadingData")
                try:
                    self._table.create_table()
                except Exception:
                    pass  # table already exists
            except Exception as e:
                logger.warning("Azure Table init failed, falling back to memory: %s", e)
                self._use_azure = False

    # ── Current book ─────────────────────────────────────────────────────────

    def get_current(self) -> CurrentBook:
        """Return the current book, falling back to the seeded default when the table is empty."""
        if self._use_azure:
            try:
                entity: dict[str, Any] = self._table.get_entity("current", "book")
                return _entity_to_current(entity)
            except Exception:
                return {**_DEFAULT_CURRENT}
        return {**_current}

    def set_current(
        self,
        title: str,
        author: str,
        thoughts: str,
        progress: int,
        since: str,
        cover: str | None = None,
    ) -> CurrentBook:
        """Persist the current book, overwriting any existing entry."""
        data: CurrentBook = {
            "title": title,
            "author": author,
            "thoughts": thoughts,
            "progress": int(progress),
            "since": since,
            "cover": cover,
        }
        if self._use_azure:
            self._table.upsert_entity({"PartitionKey": "current", "RowKey": "book", **data})
        else:
            global _current
            _current = data
        return data

    # ── Recent books ──────────────────────────────────────────────────────────

    def list_recent(self) -> list[RecentBook]:
        """Return all recently finished books; insertion order in memory, unordered from Azure."""
        if self._use_azure:
            try:
                entities: list[dict[str, Any]] = list(
                    self._table.query_entities("PartitionKey eq 'recent'")
                )
                return [_entity_to_recent(e) for e in entities]
            except Exception:
                return []
        return list(_recent)

    def add_recent(
        self,
        title: str,
        author: str,
        finished_at: str | None = None,
    ) -> RecentBook:
        """Add a finished book; defaults finished_at to the current YYYY-MM when omitted."""
        row_key = str(uuid.uuid4())
        resolved_date: str = finished_at or datetime.now(timezone.utc).strftime("%Y-%m")
        data: RecentBook = {
            "id": row_key,
            "title": title,
            "author": author,
            "finished_at": resolved_date,
        }
        if self._use_azure:
            self._table.upsert_entity(
                {
                    "PartitionKey": "recent",
                    "RowKey": row_key,
                    "title": title,
                    "author": author,
                    "finished_at": resolved_date,
                }
            )
        else:
            _recent.append(data)
        return data

    def delete_recent(self, row_key: str) -> None:
        """Remove a finished book by its ID; raises ResourceNotFoundError from Azure when missing."""
        if self._use_azure:
            self._table.delete_entity("recent", row_key)
        else:
            global _recent
            _recent[:] = [r for r in _recent if r["id"] != row_key]
