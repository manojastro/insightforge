"""BigQuery connector stub (TODO: wire google-cloud-bigquery)."""
from __future__ import annotations

from typing import Any

from .base import Connector


class BigQueryConnector(Connector):
    """BigQuery connector stub with explicit config schema and TODOs."""

    config_schema = {
        "type": "object",
        "required": ["project", "dataset"],
        "properties": {
            "project": {"type": "string"}, "dataset": {"type": "string"},
            "credentials_json": {"type": "string", "description": "Service-account JSON (store encrypted)"},
            "location": {"type": "string", "default": "US"},
        },
    }

    def _client(self):  # type: ignore[no-untyped-def]
        try:
            from google.cloud import bigquery  # type: ignore
        except ImportError as exc:
            raise NotImplementedError("TODO: pip install google-cloud-bigquery and set GOOGLE_APPLICATION_CREDENTIALS") from exc
        return bigquery.Client(project=(self.config.options or {}).get("project", self.config.host))

    def test_connection(self) -> bool:
        """Run a trivial dry-run query."""
        client = self._client()
        rows = list(client.query("SELECT 1 AS ok").result(max_results=1))
        return bool(rows) and rows[0]["ok"] == 1

    def list_tables(self) -> list[str]:
        """List tables in the configured dataset. TODO: paginate + filter."""
        raise NotImplementedError("TODO: implement list_tables via client.list_tables(dataset_ref)")

    def get_schema(self, table: str) -> list[dict[str, Any]]:
        """Return BigQuery schema fields. TODO: implement via client.get_table."""
        raise NotImplementedError("TODO: implement get_schema via client.get_table().schema")

    def sample(self, table: str, limit: int = 100) -> list[dict[str, Any]]:
        """Sample rows. TODO: implement SELECT * LIMIT query with cost controls."""
        raise NotImplementedError("TODO: implement sample with maximum_bytes_billed guard")
