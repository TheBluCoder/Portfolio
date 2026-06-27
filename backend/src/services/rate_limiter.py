"""Enforce fixed-window visitor limits with Azure Table or in-memory storage."""

from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import TYPE_CHECKING, Any, TypedDict, cast

from src.config.settings import (
    AZURE_TABLE_CONNECTION_STRING,
    RATE_LIMIT_MAX_REQUESTS,
    RATE_LIMIT_WINDOW_SECONDS,
)

if TYPE_CHECKING:
    from azure.data.tables import TableClient
else:
    TableClient = Any

try:
    from azure.data.tables import TableServiceClient as AzureTableServiceClient
    from azure.data.tables import UpdateMode
    from azure.core.exceptions import ResourceNotFoundError as AzureResourceNotFoundError
except ImportError:  # pragma: no cover - exercised when Azure SDK is absent locally
    AzureTableServiceClient = None
    UpdateMode = None
    AzureResourceNotFoundError = type("AzureResourceNotFoundError", (Exception,), {})


class RateLimitExceeded(Exception):
    """Raised when a visitor exceeds the configured request limit."""

    pass


class RateLimitRecord(TypedDict):
    """Current fixed-window state for one visitor."""

    count: int
    expires_at: datetime


class RateLimiter:
    """Track hashed visitor identities using persistent storage when configured."""

    def __init__(
        self,
        table_name: str = "RateLimits",
        max_requests: int = RATE_LIMIT_MAX_REQUESTS,
        window_seconds: int = RATE_LIMIT_WINDOW_SECONDS,
        connection_string: str | None = AZURE_TABLE_CONNECTION_STRING,
    ) -> None:
        self.table_name = table_name
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.connection_string = connection_string
        self._table_client: TableClient | None = None
        self._memory_store: dict[str, RateLimitRecord] = {}

    def visitor_key(self, ip_address: str, user_agent: str) -> str:
        """Hash an IP address and user agent into a storage-safe visitor key."""
        identity = f"{ip_address}|{user_agent}".encode("utf-8")
        return sha256(identity).hexdigest()

    def check(self, visitor_key: str) -> None:
        """Consume one request in the active window or raise RateLimitExceeded."""
        if self.connection_string and AzureTableServiceClient is not None:
            self._check_azure_table(visitor_key)
            return
        self._check_memory(visitor_key)

    def _check_memory(self, visitor_key: str) -> None:
        """Apply fixed-window limiting to process-local state."""
        now = datetime.now(timezone.utc)
        record = self._memory_store.get(visitor_key)
        if not record or now >= record["expires_at"]:
            self._memory_store[visitor_key] = {
                "count": 1,
                "expires_at": now + timedelta(seconds=self.window_seconds),
            }
            return

        if record["count"] >= self.max_requests:
            raise RateLimitExceeded()

        record["count"] += 1

    def _check_azure_table(self, visitor_key: str) -> None:
        """Apply fixed-window limiting to an Azure Table entity."""
        now = datetime.now(timezone.utc)
        table = self._get_table_client()
        try:
            entity = cast(
                dict[str, Any],
                table.get_entity(partition_key="chat", row_key=visitor_key),
            )
        except AzureResourceNotFoundError:
            entity: dict[str, Any] = {
                "PartitionKey": "chat",
                "RowKey": visitor_key,
                "Count": 0,
                "ExpiresAt": now,
            }

        expires_at = entity.get("ExpiresAt")
        if not isinstance(expires_at, datetime) or now >= expires_at:
            entity["Count"] = 1
            entity["ExpiresAt"] = now + timedelta(seconds=self.window_seconds)
        else:
            count = entity.get("Count", 0)
            if not isinstance(count, int):
                count = 0

            if count >= self.max_requests:
                raise RateLimitExceeded()
            entity["Count"] = count + 1

        table.upsert_entity(entity=entity, mode=self._merge_mode)

    @property
    def _merge_mode(self) -> Any:
        """Return the Azure Table merge mode required for counter updates."""
        if UpdateMode is None:
            raise RuntimeError("Azure Table Storage dependencies are not available.")
        return UpdateMode.MERGE

    def _get_table_client(self) -> TableClient:
        """Create the rate-limit table on demand and cache its client."""
        if self._table_client:
            return self._table_client
        if AzureTableServiceClient is None:
            raise RuntimeError("Azure Table Storage dependencies are not available.")
        if self.connection_string is None:
            raise RuntimeError("Azure Table connection string is not configured.")

        service = AzureTableServiceClient.from_connection_string(self.connection_string)
        service.create_table_if_not_exists(self.table_name)
        self._table_client = service.get_table_client(self.table_name)
        return self._table_client
