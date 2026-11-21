"""MySQL connector stub (real pymysql logic when installed, else clear TODO)."""
from __future__ import annotations

from typing import Any

from .base import Connector

try:
    import pymysql  # type: ignore

    _HAS_PYMYSQL = True
except ImportError:
    _HAS_PYMYSQL = False


class MySQLConnector(Connector):
    """MySQL connector; requires `pymysql` (TODO: add to requirements if needed)."""

    config_schema = {
        "type": "object",
        "required": ["host", "database", "username", "password"],
        "properties": {
            "host": {"type": "string"}, "port": {"type": "integer", "default": 3306},
            "database": {"type": "string"}, "username": {"type": "string"}, "password": {"type": "string"},
        },
    }

    def _connect(self):  # type: ignore[no-untyped-def]
        if not _HAS_PYMYSQL:
            raise NotImplementedError("TODO: pip install pymysql and configure MYSQL_* env vars")
        cfg = self.config
        return pymysql.connect(
            host=cfg.host, port=cfg.port or 3306, database=cfg.database,
            user=cfg.username, password=cfg.password, connect_timeout=5,
        )

    def test_connection(self) -> bool:
        """Run SELECT 1."""
        con = self._connect()
        try:
            with con.cursor() as cur:
                cur.execute("SELECT 1")
                return cur.fetchone()[0] == 1
        finally:
            con.close()

    def list_tables(self) -> list[str]:
        """List tables via SHOW TABLES."""
        con = self._connect()
        try:
            with con.cursor() as cur:
                cur.execute("SHOW TABLES")
                return [r[0] for r in cur.fetchall()]
        finally:
            con.close()

    def get_schema(self, table: str) -> list[dict[str, Any]]:
        """Describe table columns."""
        con = self._connect()
        try:
            with con.cursor() as cur:
                cur.execute(f"DESCRIBE `{table}`")
                return [{"name": r[0], "dtype": r[1]} for r in cur.fetchall()]
        finally:
            con.close()

    def sample(self, table: str, limit: int = 100) -> list[dict[str, Any]]:
        """Sample rows (dict cursor)."""
        import pymysql.cursors  # type: ignore

        con = self._connect()
        try:
            with con.cursor(pymysql.cursors.DictCursor) as cur:
                cur.execute(f"SELECT * FROM `{table}` LIMIT {max(1, min(int(limit), 1000))}")
                return list(cur.fetchall())
        finally:
            con.close()
