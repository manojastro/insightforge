"""Snowflake connector stub (TODO: wire snowflake-connector-python)."""
from __future__ import annotations

from typing import Any

from .base import Connector


class SnowflakeConnector(Connector):
    """Snowflake connector stub with explicit config schema and TODOs."""

    config_schema = {
        "type": "object",
        "required": ["account", "username", "password", "database", "warehouse"],
        "properties": {
            "account": {"type": "string"}, "username": {"type": "string"}, "password": {"type": "string"},
            "database": {"type": "string"}, "schema": {"type": "string", "default": "PUBLIC"},
            "warehouse": {"type": "string"}, "role": {"type": "string"},
        },
    }

    def _connect(self):  # type: ignore[no-untyped-def]
        try:
            import snowflake.connector  # type: ignore
        except ImportError as exc:
            raise NotImplementedError("TODO: pip install snowflake-connector-python") from exc
        o = self.config.options or {}
        return snowflake.connector.connect(
            account=o.get("account", self.config.host), user=self.config.username,
            password=self.config.password, database=self.config.database,
            schema=o.get("schema", "PUBLIC"), warehouse=o.get("warehouse"), role=o.get("role"),
            login_timeout=10,
        )

    def test_connection(self) -> bool:
        """Run SELECT 1."""
        con = self._connect()
        try:
            cur = con.cursor()
            cur.execute("SELECT 1")
            return cur.fetchone()[0] == 1
        finally:
            con.close()

    def list_tables(self) -> list[str]:
        """TODO: query INFORMATION_SCHEMA.TABLES for the configured schema."""
        raise NotImplementedError("TODO: implement SHOW TABLES / INFORMATION_SCHEMA query")

    def get_schema(self, table: str) -> list[dict[str, Any]]:
        """TODO: implement DESCRIBE TABLE."""
        raise NotImplementedError("TODO: implement DESCRIBE TABLE parsing")

    def sample(self, table: str, limit: int = 100) -> list[dict[str, Any]]:
        """TODO: implement bounded SAMPLE with warehouse auto-suspend note."""
        raise NotImplementedError("TODO: implement SELECT * LIMIT with result scanning")
