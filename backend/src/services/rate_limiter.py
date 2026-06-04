from datetime import datetime, timedelta, timezone
from hashlib import sha256
from typing import Any

from src.config.settings import (
    AZURE_TABLE_CONNECTION_STRING,
    RATE_LIMIT_MAX_REQUESTS,
    RATE_LIMIT_WINDOW_SECONDS,
)

try:
    from azure.data.tables import TableServiceClient, UpdateMode
except ImportError:  # pragma: no cover - exercised when Azure SDK is absent locally
    TableServiceClient = None
    UpdateMode = None


class RateLimitExceeded(Exception):
    pass


class RateLimiter:
    _memory_store: dict[str, dict[str, object]] = {}

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
        self._table_client = None

    def visitor_key(self, ip_address: str, user_agent: str) -> str:
        identity = f"{ip_address}|{user_agent}".encode("utf-8")
        return sha256(identity).hexdigest()

    def check(self, visitor_key: str) -> None:
        if self.connection_string and TableServiceClient:
            self._check_azure_table(visitor_key)
            return
        self._check_memory(visitor_key)

    def _check_memory(self, visitor_key: str) -> None:
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
        now = datetime.now(timezone.utc)
        table = self._get_table_client()
        try:
            entity = table.get_entity(partition_key="chat", row_key=visitor_key)
        except Exception:
            entity = {
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
            if entity.get("Count", 0) >= self.max_requests:
                raise RateLimitExceeded()
            entity["Count"] = entity.get("Count", 0) + 1

        table.upsert_entity(entity=entity, mode=UpdateMode.MERGE)

    def _get_table_client(self) -> Any:
        if self._table_client:
            return self._table_client
        service = TableServiceClient.from_connection_string(self.connection_string)
        service.create_table_if_not_exists(self.table_name)
        self._table_client = service.get_table_client(self.table_name)
        return self._table_client
