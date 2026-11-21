"""Dataset profiler: validate files, infer schema, compute quality + stats.

Supports CSV / XLSX / JSON / Parquet. Uses polars when available with a
pandas fallback. Encoding detected via chardet with utf-8 fallback.
"""
from __future__ import annotations

import json
import os
from typing import Any

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".json", ".parquet"}
MAX_PREVIEW_ROWS = 5

_NUMERIC_KINDS = {"int", "float", "number", "numeric"}


def detect_encoding(path: str) -> str:
    """Detect file encoding with chardet; fall back to utf-8."""
    try:
        import chardet  # type: ignore

        with open(path, "rb") as fh:
            raw = fh.read(100_000)
        guess = chardet.detect(raw or b"")
        enc = (guess.get("encoding") or "utf-8")
        return enc
    except Exception:
        return "utf-8"


def _load_frame(path: str) -> Any:
    """Load a file into a polars or pandas DataFrame."""
    ext = os.path.splitext(path)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"unsupported extension {ext}; allowed={sorted(ALLOWED_EXTENSIONS)}")
    # Try polars first.
    try:
        import polars as pl  # type: ignore

        if ext == ".csv":
            return pl.read_csv(path, encoding="utf8-lossy", infer_schema_length=10000)
        if ext in (".xlsx", ".xls"):
            return pl.read_excel(path)
        if ext == ".json":
            return pl.read_json(path)
        if ext == ".parquet":
            return pl.read_parquet(path)
    except ImportError:
        pass
    # Pandas fallback.
    import pandas as pd  # type: ignore

    if ext == ".csv":
        enc = detect_encoding(path)
        try:
            return pd.read_csv(path, encoding=enc)
        except UnicodeDecodeError:
            return pd.read_csv(path, encoding="utf-8", encoding_errors="replace")
    if ext in (".xlsx", ".xls"):
        return pd.read_excel(path)
    if ext == ".json":
        return pd.read_json(path)
    if ext == ".parquet":
        return pd.read_parquet(path)
    raise ValueError(f"cannot load {ext}")


def _to_records(frame: Any) -> tuple[list[str], list[dict[str, Any]], dict[str, str]]:
    """Normalise polars/pandas frame -> (columns, records, dtypes)."""
    try:
        import polars as pl  # type: ignore

        if isinstance(frame, pl.DataFrame):
            cols = list(frame.columns)
            dtypes = {c: str(frame.schema[c]) for c in cols}
            return cols, frame.head(100000).to_dicts(), dtypes
    except ImportError:
        pass
    cols = list(frame.columns)
    dtypes = {c: str(frame[c].dtype) for c in cols}
    recs = frame.head(100000).to_dict(orient="records")
    return cols, recs, dtypes


def _classify(dtype: str, name: str, samples: list[Any]) -> str:
    d = dtype.lower()
    n = name.lower()
    if any(k in n for k in ("date", "time", "created", "updated", "timestamp")):
        # Confirm at least one parseable date before claiming time type.
        import pandas as pd  # type: ignore

        try:
            s = pd.to_datetime([x for x in samples if x is not None][:20], errors="coerce", utc=True)
            if s.notna().any():
                return "time"
        except Exception:
            pass
    if "bool" in d:
        return "boolean"
    if any(k in d for k in ("int", "float", "double", "decimal", "number")):
        return "numeric"
    if "date" in d or "time" in d:
        return "time"
    if any(k in n for k in ("id", "uuid", "key", "code")):
        non_null = [x for x in samples if x is not None]
        if non_null and len(set(map(str, non_null))) >= 0.9 * len(non_null):
            return "identifier"
    return "categorical" if _is_categorical(samples) else "string"


def _is_categorical(samples: list[Any]) -> bool:
    vals = [x for x in samples if x is not None]
    if not vals:
        return False
    uniq = len(set(map(str, vals)))
    return uniq <= max(20, 0.05 * len(vals)) and uniq < len(vals)


def _pii_flags(name: str, samples: list[Any]) -> list[str]:
    """Column-level PII hints (regex-light; full scan lives in security/pii.py)."""
    try:
        import sys

        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from security.pii import detect_pii_in_values

        hits = detect_pii_in_values(samples[:200])
        col_hit = detect_pii_in_values([name])
        extra = [f"column_name:{k}" for k in col_hit]
        return sorted(set(hits + extra))
    except Exception:
        return []


def profile_file(path: str) -> dict[str, Any]:
    """Profile a dataset file and return JSON-serialisable semantic metadata."""
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    frame = _load_frame(path)
    columns, records, dtypes = _to_records(frame)
    n_rows = len(records)

    col_profiles: list[dict[str, Any]] = []
    for col in columns:
        vals = [r.get(col) for r in records]

        def _is_missing(v: Any) -> bool:
            if v is None:
                return True
            if isinstance(v, float):
                import math

                return math.isnan(v)
            try:
                import pandas as pd  # type: ignore

                if pd.isna(v):
                    return True
            except Exception:
                pass
            return str(v).strip() == "" or str(v).lower() == "nan"

        non_null = [v for v in vals if not _is_missing(v)]
        missing = n_rows - len(non_null)
        dtype = dtypes.get(col, "unknown")
        ctype = _classify(dtype, col, non_null[:500])
        entry: dict[str, Any] = {
            "name": col,
            "dtype": dtype,
            "semantic_type": ctype,
            "missing": missing,
            "missing_rate": (missing / n_rows) if n_rows else 0.0,
            "distinct": len(set(map(str, non_null))),
            "sample": non_null[:3],
            "pii_flags": _pii_flags(col, [str(v) for v in non_null[:200]]),
        }
        if ctype == "numeric":
            nums = []
            for v in non_null:
                try:
                    nums.append(float(v))  # type: ignore[arg-type]
                except (TypeError, ValueError):
                    continue
            if nums:
                import math
                import statistics as _st

                nums = [x for x in nums if not (isinstance(x, float) and (math.isnan(x) or math.isinf(x)))]
                if nums:
                    entry["descriptives"] = {
                        "mean": sum(nums) / len(nums),
                        "median": _st.median(nums),
                        "std": _st.pstdev(nums) if len(nums) > 1 else 0.0,
                        "min": min(nums),
                        "max": max(nums),
                    }
        if ctype in ("categorical", "string"):
            from collections import Counter

            entry["top_values"] = Counter(map(str, non_null)).most_common(10)
        col_profiles.append(entry)

    # Duplicates over full rows.
    seen: set[str] = set()
    dupes = 0
    for r in records:
        key = json.dumps(r, sort_keys=True, default=str)
        if key in seen:
            dupes += 1
        seen.add(key)

    # Numeric correlations (pairwise Pearson, capped at 8 numeric cols).
    correlations: dict[str, float] = {}
    try:
        from .statistics import correlation as _corr

        num_cols = [c["name"] for c in col_profiles if c["semantic_type"] == "numeric"][:8]
        for i in range(len(num_cols)):
            for j in range(i + 1, len(num_cols)):
                xi = [r.get(num_cols[i]) for r in records]
                yi = [r.get(num_cols[j]) for r in records]
                v = _corr(xi, yi)
                if v is not None:
                    correlations[f"{num_cols[i]}~{num_cols[j]}"] = round(v, 4)
    except Exception:
        correlations = {}

    # Outliers per numeric column (cap flags at 50 indices).
    outliers: dict[str, list[int]] = {}
    try:
        from .statistics import outlier_iqr_zscore as _out

        for c in col_profiles:
            if c["semantic_type"] != "numeric":
                continue
            vals = [r.get(c["name"]) for r in records]
            res = _out(vals)
            if res["indices"]:
                outliers[c["name"]] = res["indices"][:50]
    except Exception:
        outliers = {}

    time_fields = [c["name"] for c in col_profiles if c["semantic_type"] == "time"]
    identifiers = [c["name"] for c in col_profiles if c["semantic_type"] == "identifier"]

    return {
        "file": os.path.basename(path),
        "format": os.path.splitext(path)[1].lower().lstrip("."),
        "encoding": detect_encoding(path),
        "row_count": n_rows,
        "column_count": len(columns),
        "columns": col_profiles,
        "duplicate_rows": dupes,
        "time_fields": time_fields,
        "identifiers": identifiers,
        "correlations": correlations,
        "outliers": outliers,
        "preview": records[:MAX_PREVIEW_ROWS],
    }
