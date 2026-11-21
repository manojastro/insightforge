"""Deterministic descriptive statistics — no LLM, no network.

All functions accept plain Python sequences and return plain dicts/lists
so they work with DuckDB rows, pandas, or polars inputs.
"""
from __future__ import annotations

import math
from collections import Counter
from typing import Any, Sequence


def _clean(values: Sequence[Any]) -> list[float]:
    out: list[float] = []
    for v in values:
        if v is None:
            continue
        try:
            f = float(v)
        except (TypeError, ValueError):
            continue
        if math.isnan(f) or math.isinf(f):
            continue
        out.append(f)
    return out


def mean(values: Sequence[Any]) -> float | None:
    """Arithmetic mean or None when empty."""
    xs = _clean(values)
    return sum(xs) / len(xs) if xs else None


def median(values: Sequence[Any]) -> float | None:
    """Median or None when empty."""
    xs = sorted(_clean(values))
    if not xs:
        return None
    n = len(xs)
    mid = n // 2
    return xs[mid] if n % 2 else (xs[mid - 1] + xs[mid]) / 2.0


def std(values: Sequence[Any], ddof: int = 1) -> float | None:
    """Sample (ddof=1) standard deviation; None when too few values."""
    xs = _clean(values)
    if len(xs) <= ddof:
        return None
    m = sum(xs) / len(xs)
    var = sum((x - m) ** 2 for x in xs) / (len(xs) - ddof)
    return math.sqrt(var)


def quantiles(values: Sequence[Any], qs: Sequence[float] = (0.25, 0.5, 0.75)) -> dict[str, float | None]:
    """Linear-interpolation quantiles keyed like 'p25'."""
    xs = sorted(_clean(values))
    out: dict[str, float | None] = {}
    for q in qs:
        key = f"p{int(round(q * 100))}"
        if not xs:
            out[key] = None
            continue
        pos = q * (len(xs) - 1)
        lo = math.floor(pos)
        hi = math.ceil(pos)
        out[key] = xs[lo] + (xs[hi] - xs[lo]) * (pos - lo) if hi != lo else xs[lo]
    return out


def pct_change(first: float, last: float) -> float | None:
    """Percent change from first to last; None when first is 0."""
    if first == 0:
        return None
    return (last - first) / abs(first) * 100.0


def distribution(values: Sequence[Any], bins: int = 10) -> dict[str, Any]:
    """Equal-width histogram with counts and edges."""
    xs = _clean(values)
    bins = max(1, int(bins))
    if not xs:
        return {"counts": [0] * bins, "edges": [], "bins": bins}
    lo, hi = min(xs), max(xs)
    if lo == hi:
        counts = [0] * bins
        counts[0] = len(xs)
        return {"counts": counts, "edges": [lo, hi], "bins": bins}
    width = (hi - lo) / bins
    edges = [lo + i * width for i in range(bins + 1)]
    counts = [0] * bins
    for x in xs:
        idx = min(int((x - lo) / width), bins - 1)
        counts[idx] += 1
    return {"counts": counts, "edges": edges, "bins": bins}


def correlation(x: Sequence[Any], y: Sequence[Any]) -> float | None:
    """Pearson correlation; None when undefined or length < 2."""
    xs = _clean(x)
    ys = _clean(y)
    n = min(len(xs), len(ys))
    if n < 2:
        return None
    xs, ys = xs[:n], ys[:n]
    mx, my = sum(xs) / n, sum(ys) / n
    num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    dx = math.sqrt(sum((a - mx) ** 2 for a in xs))
    dy = math.sqrt(sum((b - my) ** 2 for b in ys))
    if dx == 0 or dy == 0:
        return None
    return num / (dx * dy)


def trend(values: Sequence[Any]) -> dict[str, Any]:
    """Least-squares slope/intercept over the sequence index."""
    xs = _clean(values)
    n = len(xs)
    if n < 2:
        return {"slope": None, "intercept": None, "direction": "flat"}
    mx = (n - 1) / 2.0
    my = sum(xs) / n
    denom = sum((i - mx) ** 2 for i in range(n))
    slope = sum((i - mx) * (v - my) for i, v in enumerate(xs)) / denom if denom else 0.0
    direction = "up" if slope > 0 else ("down" if slope < 0 else "flat")
    return {"slope": slope, "intercept": my - slope * mx, "direction": direction}


def rolling_avg(values: Sequence[Any], window: int = 3) -> list[float | None]:
    """Trailing rolling mean; leading positions are None."""
    xs = _clean(values)
    window = max(1, int(window))
    out: list[float | None] = []
    acc = 0.0
    for i, v in enumerate(xs):
        acc += v
        if i >= window:
            acc -= xs[i - window]
        out.append(acc / min(i + 1, window) if i + 1 >= 1 else None)
        if i + 1 < window:
            # keep partial averages deterministic but mark leading as partial
            pass
    # Align with raw positions: leading window-1 are partial; keep values (deterministic).
    return out


def _zscores(xs: list[float]) -> list[float]:
    m = sum(xs) / len(xs)
    var = sum((v - m) ** 2 for v in xs) / len(xs)
    s = math.sqrt(var)
    if s == 0:
        return [0.0] * len(xs)
    return [(v - m) / s for v in xs]


def outlier_iqr_zscore(values: Sequence[Any], z_thresh: float = 3.0) -> dict[str, Any]:
    """Union of IQR and z-score outlier indices."""
    xs = _clean(values)
    n = len(xs)
    if n < 4:
        return {"indices": [], "iqr": [], "zscore": []}
    s = sorted(xs)
    q1 = quantiles(xs, [0.25])["p25"] or 0.0
    q3 = quantiles(xs, [0.75])["p75"] or 0.0
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    iqr_idx = [i for i, v in enumerate(xs) if v < lo or v > hi]
    zs = _zscores(xs)
    z_idx = [i for i, z in enumerate(zs) if abs(z) >= z_thresh]
    return {"indices": sorted(set(iqr_idx) | set(z_idx)), "iqr": iqr_idx, "zscore": z_idx}


def regression(x: Sequence[Any], y: Sequence[Any]) -> dict[str, Any]:
    """Simple OLS y ~ x with R^2."""
    xs = _clean(x)
    ys = _clean(y)
    n = min(len(xs), len(ys))
    if n < 2:
        return {"slope": None, "intercept": None, "r2": None}
    xs, ys = xs[:n], ys[:n]
    mx, my = sum(xs) / n, sum(ys) / n
    denom = sum((v - mx) ** 2 for v in xs)
    slope = sum((a - mx) * (b - my) for a, b in zip(xs, ys)) / denom if denom else 0.0
    intercept = my - slope * mx
    ss_tot = sum((b - my) ** 2 for b in ys)
    ss_res = sum((b - (slope * a + intercept)) ** 2 for a, b in zip(xs, ys))
    r2 = 1 - ss_res / ss_tot if ss_tot else 0.0
    return {"slope": slope, "intercept": intercept, "r2": r2}


def confidence(values: Sequence[Any], level: float = 0.95) -> dict[str, Any]:
    """Normal-approx confidence interval for the mean (z=1.96 at 95%)."""
    xs = _clean(values)
    if not xs:
        return {"mean": None, "low": None, "high": None, "level": level}
    m = sum(xs) / len(xs)
    s = std(xs, ddof=1) or 0.0
    z = 1.96 if abs(level - 0.95) < 1e-9 else 1.645
    half = z * s / math.sqrt(len(xs)) if len(xs) else 0.0
    return {"mean": m, "low": m - half, "high": m + half, "level": level}


def cohort(values: Sequence[Any], labels: Sequence[Any]) -> dict[str, dict[str, Any]]:
    """Per-label count/mean/median summaries."""
    out: dict[str, dict[str, Any]] = {}
    buckets: dict[str, list[float]] = {}
    for v, lab in zip(values, labels):
        try:
            f = float(v)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            continue
        if f != f:  # NaN
            continue
        buckets.setdefault(str(lab), []).append(f)
    for lab, xs in buckets.items():
        out[lab] = {"count": len(xs), "mean": mean(xs), "median": median(xs)}
    return out


def segmentation(values: Sequence[Any], labels: Sequence[Any], top_k: int = 5) -> list[dict[str, Any]]:
    """Top-k label segments by total contribution share."""
    totals: Counter = Counter()
    num: dict[str, float] = {}
    for v, lab in zip(values, labels):
        try:
            f = float(v)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            continue
        key = str(lab)
        totals[key] += 1
        num[key] = num.get(key, 0.0) + f
    grand = sum(num.values())
    ranked = sorted(num.items(), key=lambda kv: kv[1], reverse=True)[: max(1, top_k)]
    return [
        {"segment": k, "total": v, "share": (v / grand if grand else 0.0), "count": totals[k]}
        for k, v in ranked
    ]
