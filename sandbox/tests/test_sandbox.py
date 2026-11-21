"""Sandbox policy tests (no network, DuckDB in-memory only)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sandbox.duckdb_sandbox import SandboxError, execute_sandbox, validate_sql  # noqa: E402


def _exec(sql, tables=None, **kw):
    return execute_sandbox(sql, tables=tables or {"data": [{"a": 1, "b": 2}]}, **kw)


def test_allow_select():
    r = _exec("SELECT 1 AS x", tables={})
    assert r["columns"] == ["x"] and r["rows"] == [[1]]


def test_allow_with():
    r = _exec("WITH t AS (SELECT 1 AS x) SELECT * FROM t", tables={})
    assert r["rows"] == [[1]]


def test_block_delete():
    with pytest.raises(SandboxError):
        _exec("DELETE FROM data")


def test_block_drop():
    with pytest.raises(SandboxError):
        _exec("DROP TABLE data")


def test_block_insert():
    with pytest.raises(SandboxError):
        _exec("INSERT INTO data VALUES (1)")


def test_block_copy_to_file():
    with pytest.raises(SandboxError):
        _exec("COPY data TO '/tmp/x.csv'")


def test_block_attach():
    with pytest.raises(SandboxError):
        _exec("ATTACH '/tmp/x.db' AS foo")


def test_block_pragma():
    with pytest.raises(SandboxError):
        _exec("PRAGMA show('data')")


def test_block_filesystem_fn():
    with pytest.raises(SandboxError):
        _exec("SELECT * FROM read_csv('/tmp/x.csv')", tables={})


def test_table_allowlist():
    with pytest.raises(SandboxError):
        execute_sandbox("SELECT * FROM secret", tables={"data": [{"a": 1}]}, allowed_tables=["data"])


def test_row_limit():
    rows = [{"a": i} for i in range(10)]
    r = execute_sandbox("SELECT * FROM data", tables={"data": rows}, row_limit=3)
    assert r["row_count"] == 10 and len(r["rows"]) == 3 and r["truncated"] is True


def test_column_limit():
    with pytest.raises(SandboxError):
        validate_sql("SELECT 1 AS a, 2 AS b, 3 AS c", allowed_tables=[], column_limit=2)


def test_timeout_or_stacked():
    with pytest.raises(SandboxError):
        _exec("SELECT 1; SELECT 2", tables={})


def test_update_blocked():
    with pytest.raises(SandboxError):
        _exec("UPDATE data SET a = 1")
