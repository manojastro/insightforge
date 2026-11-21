"""Postgres connector (real psycopg2 logic, lightweight)."""
from __future__ import annotations

from typing import Any

from .base import Connector, ConnectorConfig

try:
    import psycopg2  # type: ignore
    import psycopg2.extras  # type: ignore

    _HAS_PSYCOPG2 = True
except ImportError:
    _HAS_PSYCOPG2 = False


class PostgresConnector(Connector):
    """PostgreSQL connector using psycopg2."""

    config_schema = {
        "type": "object",
        "required": ["host", "database", "username", "password"],
        "properties": {
            "host": {"type": "string"}, "port": {"type": "integer", "default": 5432},
            "database": {"type": "string"}, "username": {"type": "string"},
            "password": {"type": "string"}, "sslmode": {"type": "string", "default": "prefer"},
        },
    }

    def _connect(self):  # type: ignore[no-untyped-def]
        if not _HAS_PSYCOPG2:
            raise NotImplementedError("psycopg2 not installed; TODO: pip install psycopg2-binary")
        cfg: ConnectorConfig = self.config
        return psycopg2.connect(
            host=cfg.host, port=cfg.port or 5432, dbname=cfg.database,
            user=cfg.username, password=cfg.password,
            sslmode=(cfg.options or {}).get("sslmode", "prefer"),
            connect_timeout=5,
        )

    def test_connection(self) -> bool:
        """Run SELECT 1."""
        con = self._connect()
        try:
            with con.cursor() as cur:
                cur.execute("SELECT 1")
                return cur.fetchone() == (1,)
        finally:
            con.close()

    def list_tables(self) -> list[str]:
        """List base tables in the public schema."""
        con = self._connect()
        try:
            with con.cursor() as cur:
                cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY 1")
                return [r[0] for r in cur.fetchall()]
        finally:
            con.close()

    def get_schema(self, table: str) -> list[dict[str, Any]]:
        """Return column names + types from information_schema."""
        con = self._connect()
        try:
            with con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:  # type: ignore[attr-defined]
                cur.execute(
                    "SELECT column_name AS name, data_type AS dtype FROM information_schema.columns "
                    "WHERE table_name=%s ORDER BY ordinal_position",
                    (table,),
                )
                return list(cur.fetchall())
        finally:
            con.close()

    def sample(self, table: str, limit: int = 100) -> list[dict[str, Any]]:
        """Sample rows with a quoted identifier and bounded limit."""
        if not table.replace("_", "").isalnum():
            raise ValueError("unsafe table name")
        limit = max(1, min(int(limit), 1000))
        con = self._connect()
        try:
            with con.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:  # type: ignore[attr-defined]
                cur.execute(f'SELECT * FROM "{table}" LIMIT {limit}')
                return list(cur.fetchall())
        finally:
            con.close()
