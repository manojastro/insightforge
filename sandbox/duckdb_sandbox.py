"""Read-only DuckDB sandbox with sqlglot parsing, allowlists, and limits.

Policy:
- Allowed statement types: SELECT / WITH / VALUES (EXPLAIN of those is unwrapped
  and validated, never executed as EXPLAIN side-channel).
- Blocked: INSERT/UPDATE/DELETE/DROP/CREATE/ALTER/COPY/ATTACH/INSTALL/LOAD/
  PRAGMA/filesystem functions (read_csv, read_parquet, ...), semicolons stacking.
- Tables restricted to an explicit allowlist for the current dataset.
- Row limit 5000, column limit 50, statement timeout enforced; DuckDB runs with
  threads=1 and no external-file access by construction (no COPY/FROM file).
"""
from __future__ import annotations

import re
import threading
import time
from typing import Any

import sqlglot
import sqlglot.expressions as exp

ROW_LIMIT_DEFAULT = 5000
COLUMN_LIMIT_DEFAULT = 50
TIMEOUT_S_DEFAULT = 15

_BLOCKED_KEYWORDS = (
    "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "COPY",
    "ATTACH", "DETACH", "INSTALL", "LOAD", "PRAGMA", "VACUUM", "CHECKPOINT",
    "CALL", "GRANT", "REVOKE",
)
_BLOCKED_FUNCTIONS = (
    "read_csv", "read_csv_auto", "read_parquet", "read_json", "read_excel",
    "parquet_scan", "csv_scan", "copy_to", "write_parquet", "write_csv",
)


class SandboxError(ValueError):
    """Raised when SQL violates sandbox policy."""


def _strip_comments(sql: str) -> str:
    sql = re.sub(r"--.*?$", "", sql, flags=re.M)
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.S)
    return sql.strip()


def validate_sql(sql: str, allowed_tables: list[str] | None = None, column_limit: int = COLUMN_LIMIT_DEFAULT) -> exp.Expression:
    """Parse with sqlglot and enforce the read-only policy. Returns the AST."""
    cleaned = _strip_comments(sql)
    if not cleaned:
        raise SandboxError("empty SQL")
    if ";" in cleaned.strip().rstrip(";"):
        # Allow a single trailing semicolon only.
        body = cleaned.strip()
        if body.endswith(";"):
            body = body[:-1]
        if ";" in body:
            raise SandboxError("multiple statements are not allowed")
        cleaned = body
    upper = cleaned.upper()
    for kw in _BLOCKED_KEYWORDS:
        if re.search(rf"\b{kw}\b", upper):
            raise SandboxError(f"blocked keyword: {kw}")
    for fn in _BLOCKED_FUNCTIONS:
        if re.search(rf"\b{fn}\s*\(", cleaned, re.I):
            raise SandboxError(f"blocked filesystem function: {fn}")
    if re.search(r"://|\\\\", cleaned):
        raise SandboxError("URLs/paths are not allowed")

    try:
        tree = sqlglot.parse_one(cleaned, read="duckdb")
    except Exception as exc:
        raise SandboxError(f"parse error: {exc}") from exc

    # Unwrap EXPLAIN — validate the inner query, return inner for execution.
    # Version-agnostic: sqlglot class name differs across releases.
    ExplainCls = getattr(exp, "Explain", None)
    if ExplainCls is not None and isinstance(tree, ExplainCls):
        inner = getattr(tree, "this", None) or getattr(tree, "expression", None)
        if inner is not None:
            tree = inner
    elif type(tree).__name__.lower() == "explain":
        inner = getattr(tree, "this", None) or getattr(tree, "expression", None)
        if inner is not None:
            tree = inner

    _allowed_types = tuple(
        t for t in (
            getattr(exp, "Select", None),
            getattr(exp, "Union", None),
            getattr(exp, "Values", None),
            getattr(exp, "With", None),
        )
        if t is not None
    )
    if _allowed_types and not isinstance(tree, _allowed_types):
        raise SandboxError(f"only SELECT/WITH/VALUES queries allowed, got {type(tree).__name__}")

    # Table allowlist (ignore CTE names defined in WITH clause).
    if allowed_tables is not None:
        allowed = {t.lower() for t in allowed_tables}
        cte_names: set[str] = set()
        try:
            CTE = getattr(exp, "CTE", None)
            if CTE is not None:
                for cte in tree.find_all(CTE):
                    alias = getattr(getattr(cte, "alias", None), "this", None)
                    name = cte.args.get("alias", None)
                    # cte.alias returns alias expression; extract string
                    try:
                        alias_name = cte.alias if isinstance(cte.alias, str) else None
                    except Exception:
                        alias_name = None
                    if alias_name:
                        cte_names.add(alias_name.lower())
                    elif hasattr(cte, "alias") and cte.args.get("alias"):
                        a = cte.args.get("alias")
                        # a may be TableAlias; get .this
                        this = getattr(a, "this", None)
                        if this is not None and hasattr(this, "name"):
                            try:
                                cte_names.add(this.name.lower())
                            except Exception:
                                pass
        except Exception:
            pass
        found = {t.name.lower() for t in tree.find_all(exp.Table) if t.name}
        unknown = (found - allowed) - cte_names
        if unknown:
            raise SandboxError(f"tables not in allowlist: {sorted(unknown)}")

    # Column limit (top-level named selects; * counts as 1 here, enforced post-exec too).
    if isinstance(tree, exp.Select):
        n = len(tree.expressions)
        if n > column_limit:
            raise SandboxError(f"column limit exceeded: {n} > {column_limit}")
    return tree


def execute_sandbox(
    sql: str,
    tables: dict[str, Any] | None = None,
    allowed_tables: list[str] | None = None,
    row_limit: int = ROW_LIMIT_DEFAULT,
    column_limit: int = COLUMN_LIMIT_DEFAULT,
    timeout_s: int | float = TIMEOUT_S_DEFAULT,
) -> dict[str, Any]:
    """Validate then execute SQL against an in-memory DuckDB with limits.

    `tables` maps table name -> data source: a pandas/polars DataFrame,
    a list of dicts, or a DuckDB relation name already registered by the
    caller. When None, an empty in-memory DB is used (useful for SELECT 1).
    """
    allow = allowed_tables if allowed_tables is not None else (list(tables.keys()) if tables else [])
    tree = validate_sql(sql, allowed_tables=allow, column_limit=column_limit)
    safe_sql = tree.sql(dialect="duckdb")

    import duckdb  # local import so module import stays light without duckdb

    holder: dict[str, Any] = {}
    err: list[BaseException] = []

    def _run() -> None:
        try:
            con = duckdb.connect(":memory:")
            try:
                con.execute("SET threads=1")
                # Register provided tables.
                for name, data in (tables or {}).items():
                    try:
                        con.register(name, data)
                    except Exception:
                        # list-of-dicts fallback via pandas
                        try:
                            import pandas as pd  # type: ignore

                            con.register(name, pd.DataFrame(data))
                        except Exception as exc2:
                            raise SandboxError(f"cannot register table {name}: {exc2}") from exc2
                start = time.perf_counter()
                rel = con.execute(safe_sql).fetchall()
                cols = [d[0] for d in con.description] if con.description else []
                dur = (time.perf_counter() - start) * 1000.0
                if len(cols) > column_limit:
                    raise SandboxError(f"column limit exceeded: {len(cols)} > {column_limit}")
                truncated = rel[:row_limit]
                holder.update({
                    "columns": cols,
                    "rows": [list(r) for r in truncated],
                    "row_count": len(rel),
                    "truncated": len(rel) > row_limit,
                    "duration_ms": dur,
                })
            finally:
                con.close()
        except BaseException as exc:  # noqa: BLE001 — propagate via err list
            err.append(exc)

    th = threading.Thread(target=_run, daemon=True)
    th.start()
    th.join(timeout=timeout_s)
    if th.is_alive():
        raise SandboxError(f"query timed out after {timeout_s}s")
    if err:
        e = err[0]
        if isinstance(e, SandboxError):
            raise e
        raise SandboxError(f"execution error: {e}")
    return holder
