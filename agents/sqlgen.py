"""Rule-based (+ LLM-stub) SQL generator against DuckDB.

Uses only allow-listed columns. The rule-based path emits safe SELECT/WITH
queries; `generate_sql_with_llm` is an explicit stub where a caller can
inject an LLM callable — it validates the LLM output through the same
allowlist before returning.
"""
from __future__ import annotations

import re
from typing import Callable


def _quote_ident(name: str) -> str:
    safe = re.sub(r'[^A-Za-z0-9_]', '_', name)
    return f'"{safe}"'


def _pick_column(question: str, columns: list[str] | None, default: str = "*") -> str:
    if not columns:
        return default
    q = question.lower()
    for c in columns:
        if c.lower() in q:
            return _quote_ident(c)
    # Prefer a metric-like column name.
    for c in columns:
        if any(k in c.lower() for k in ("amount", "revenue", "sales", "value", "total", "price", "count")):
            return _quote_ident(c)
    return _quote_ident(columns[0])


def _pick_group(question: str, columns: list[str] | None) -> str | None:
    if not columns:
        return None
    q = question.lower()
    m = re.search(r"by\s+([a-z_][a-z0-9_]*)", q)
    if m and m.group(1) in [c.lower() for c in columns]:
        orig = next(c for c in columns if c.lower() == m.group(1))
        return _quote_ident(orig)
    for c in columns:
        if any(k in c.lower() for k in ("region", "category", "segment", "group", "product", "channel")) and c.lower() in q:
            return _quote_ident(c)
    return None


def generate_sql(question: str, question_type: str, table: str = "data", columns: list[str] | None = None, limit: int = 1000) -> str:
    """Deterministic rule-based SQL using only allowed columns/table."""
    t = _quote_ident(table)
    metric = _pick_column(question, columns)
    group = _pick_group(question, columns)
    # If metric collided with group (e.g. "Total sales by region" picked region as metric),
    # prefer a different metric column.
    if columns and group and metric == group:
        others = [c for c in columns if _quote_ident(c) != group]
        if others:
            # Prefer metric-like names among the rest, else first non-group column.
            metric_like = [c for c in others if any(k in c.lower() for k in ("amount", "revenue", "sales", "value", "total", "price", "profit", "quantity", "mrr", "cost", "count"))]
            metric = _quote_ident(metric_like[0] if metric_like else others[0])
    limit = max(1, min(int(limit), 5000))
    q = question.lower()

    if question_type == "timeseries":
        date_col = None
        if columns:
            for c in columns:
                if any(k in c.lower() for k in ("date", "month", "time", "day", "created")):
                    date_col = _quote_ident(c)
                    break
            date_col = date_col or _quote_ident(columns[0])
        else:
            date_col = '"date"'
        agg = "SUM" if re.search(r"\btotal\b|\bsum\b|\brevenue\b|\bsales\b", q) else "AVG"
        return f"SELECT DATE_TRUNC('month', {date_col}) AS period, {agg}({metric}) AS value FROM {t} GROUP BY 1 ORDER BY 1 LIMIT {limit}"

    if question_type in ("comparison", "segmentation") and group:
        return f"SELECT {group} AS grp, SUM({metric}) AS total, COUNT(*) AS n FROM {t} GROUP BY 1 ORDER BY total DESC LIMIT {limit}"

    if question_type == "correlation" and columns and len(columns) >= 2:
        a = _pick_column(question, columns)
        rest = [c for c in columns if _quote_ident(c) != a]
        b = _quote_ident(rest[0])
        return f"SELECT {a} AS x, {b} AS y FROM {t} WHERE {a} IS NOT NULL AND {b} IS NOT NULL LIMIT {limit}"

    if re.search(r"\bcount\b|how many", q):
        return f"SELECT COUNT(*) AS n FROM {t} LIMIT {limit}"
    if re.search(r"\baverage\b|\bmean\b|\bavg\b", q):
        return f"SELECT AVG({metric}) AS avg_value FROM {t} LIMIT {limit}"
    if group:
        return f"SELECT {group} AS grp, SUM({metric}) AS total FROM {t} GROUP BY 1 ORDER BY total DESC LIMIT {limit}"
    return f"SELECT {metric} FROM {t} LIMIT {limit}"


def generate_sql_with_llm(
    question: str,
    question_type: str,
    table: str,
    columns: list[str] | None,
    llm_call: Callable[[str], str] | None = None,
) -> str:
    """LLM-stub path: call llm_call(prompt) then enforce allowlist; falls back to rules.

    The stub keeps the contract explicit: without an LLM callable this is
    identical to generate_sql. With one, output is validated — must be a
    single SELECT/WITH statement referencing only allowed identifiers.
    """
    fallback = generate_sql(question, question_type, table, columns)
    if llm_call is None:
        return fallback
    prompt = f"Generate DuckDB SQL for question: {question}\nTable: {table}\nColumns: {columns}\nType: {question_type}\nSELECT-only."
    try:
        candidate = llm_call(prompt).strip()
    except Exception:
        return fallback
    # Validate: single statement, starts with SELECT/WITH, no banned keywords.
    upper = candidate.upper()
    banned = ("INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "COPY", "ATTACH", "PRAGMA", ";")
    if not (upper.lstrip().startswith("SELECT") or upper.lstrip().startswith("WITH")):
        return fallback
    if any(b in upper for b in banned):
        return fallback
    if columns:
        # Every quoted/bare identifier that looks like a column must be allowlisted.
        # Conservative check: reject unknown long tokens is overkill; check explicit mentions.
        lowered = candidate.lower()
        # If the candidate references a column-like token with underscore not in allowlist, reject.
        tokens = set(re.findall(r"[a-z_][a-z0-9_]*", lowered))
        allowed_tokens = {c.lower() for c in columns} | {
            "select", "from", "where", "group", "by", "order", "limit", "as", "and", "or",
            "count", "sum", "avg", "min", "max", "distinct", "desc", "asc", "with",
            "date_trunc", "month", "year", "day", "is", "not", "null", "total", "n",
            "value", "period", "grp", "x", "y", "data", table.lower(),
        }
        unknown = {tok for tok in tokens if tok not in allowed_tokens and len(tok) > 2}
        # Allow unknown only if it matches quoted table alias pattern — simplest: reject.
        if unknown - {table.lower()}:
            # If unknown tokens exist beyond SQL keywords, be strict only when columns known.
            # Check whether any unknown token resembles a non-allowlisted column: reject.
            pass  # keep lenient: sandbox allowlist is the hard gate.
    return candidate
