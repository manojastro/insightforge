"""Connector ABC with encrypted-config design."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ConnectorConfig:
    """Connection config; secrets should be encrypted at rest (env/KMS).

    Design: callers pass plaintext from a secrets manager; `redacted()` is
    safe to log/store. TODO(prod): envelope-encrypt password/private_key
    with KMS before persisting to the connectors table.
    """

    host: str = ""
    port: int = 0
    database: str = ""
    username: str = ""
    password: str = ""
    options: dict[str, Any] | None = None

    def redacted(self) -> dict[str, Any]:
        """Return a log-safe view with secrets masked."""
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "username": self.username,
            "password": "***",
            "options": self.options or {},
        }


class Connector(ABC):
    """Abstract warehouse connector."""

    config_schema: dict[str, Any] = {}

    def __init__(self, config: ConnectorConfig):
        self.config = config

    @abstractmethod
    def test_connection(self) -> bool:
        """Return True when a lightweight probe query succeeds."""

    @abstractmethod
    def list_tables(self) -> list[str]:
        """List available tables/schemas."""

    @abstractmethod
    def get_schema(self, table: str) -> list[dict[str, Any]]:
        """Return [{name, dtype}] for a table."""

    @abstractmethod
    def sample(self, table: str, limit: int = 100) -> list[dict[str, Any]]:
        """Return up to `limit` sample rows."""
