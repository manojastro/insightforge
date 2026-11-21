"""Databricks connector stub (TODO: wire databricks-sql-connector)."""
from __future__ import annotations

from typing import Any

from .base import Connector


class DatabricksConnector(Connector):
    """Databricks SQL warehouse connector stub with explicit config schema."""

    config_schema = {
        "type": "object",
        "required": ["host", "http_path", "token"],
        "properties": {
            "host": {"type": "string"}, "http_path": {"type": "string"},
            "token": {"type": "string", "description": "PAT — store encrypted"},
            "catalog": {"type": "string", "default": "main"}, "schema": {"type": "string", "default": "default"},
        },
    }

    def _connect(self):  # type: ignore[no-untyped-def]
        try:
            from databricks import sql  # type: ignore
        except ImportError as exc:
            raise NotImplementedError("TODO: pip install databricks-sql-connector") from exc
        o = self.config.options or {}
        return sql.connect(
            server_hostname=self.config.host, http_path=o.get("http_path", ""),
            access_token=o.get("token", self.config.password),
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
        """TODO: implement SHOW TABLES with catalog/schema scoping."""
        raise NotImplementedError("TODO: implement SHOW TABLES IN catalog.schema")

    def get_schema(self, table: str) -> list[dict[str, Any]]:
        """TODO: implement DESCRIBE TABLE."""
        raise NotImplementedError("TODO: implement DESCRIBE TABLE parsing")

    def sample(self, table: str, limit: int = 100) -> list[dict[str, Any]]:
        """TODO: implement bounded SELECT with Unity Catalog guardrails."""
        raise NotImplementedError("TODO: implement SELECT * LIMIT with column masking note")
