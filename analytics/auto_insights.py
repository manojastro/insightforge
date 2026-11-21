"""Deterministic auto-insights over a numeric series.

Rule set (all deterministic, no LLM):
- largest increase / decrease (consecutive deltas)
- top contributors (share of total when labels given)
- anomaly (IQR/z-score outliers)
- changepoint (max shift in rolling means)
- high correlation (needs 'other' series in context)
- quality issue (NaN/gaps, flat series)
- unusual segment (max cohort deviation from global mean)
"""
from __future__ import annotations

from typing import Any, Sequence

from .statistics import cohort, correlation, mean, outlier_iqr_zscore, pct_change, trend


def _num(xs: Sequence[Any]) -> list[float]:
    out: list[float] = []
    for v in xs:
        try:
            f = float(v)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            continue
        if f == f:  # not NaN
            out.append(f)
    return out


def generate_insights(
    series: Sequence[Any],
    labels: Sequence[Any] | None = None,
    other: Sequence[Any] | None = None,
    other_name: str = "other",
) -> list[dict[str, Any]]:
    """Generate a ranked list of insight dicts with kind/title/body/confidence."""
    xs = _num(series)
    insights: list[dict[str, Any]] = []
    if len(xs) < 2:
        return [{"kind": "quality_issue", "title": "Not enough data", "body": "Series has fewer than 2 numeric points.", "confidence": 0.9}]

    # Largest increase / decrease.
    deltas = [xs[i + 1] - xs[i] for i in range(len(xs) - 1)]
    i_max, i_min = max(range(len(deltas)), key=lambda i: deltas[i]), min(range(len(deltas)), key=lambda i: deltas[i])
    if deltas[i_max] > 0:
        insights.append({
            "kind": "largest_increase",
            "title": f"Largest increase at step {i_max + 1} (+{deltas[i_max]:.2f})",
            "body": f"Value rose from {xs[i_max]:.2f} to {xs[i_max + 1]:.2f} (+{(pct_change(xs[i_max], xs[i_max + 1]) or 0):.1f}%).",
            "confidence": 0.95,
            "index": i_max + 1,
        })
    if deltas[i_min] < 0:
        insights.append({
            "kind": "largest_decrease",
            "title": f"Largest decrease at step {i_min + 1} ({deltas[i_min]:.2f})",
            "body": f"Value fell from {xs[i_min]:.2f} to {xs[i_min + 1]:.2f} ({(pct_change(xs[i_min], xs[i_min + 1]) or 0):.1f}%).",
            "confidence": 0.95,
            "index": i_min + 1,
        })

    # Top contributors.
    if labels and len(labels) == len(series):
        totals: dict[str, float] = {}
        for v, lab in zip(_num(series), labels):
            totals[str(lab)] = totals.get(str(lab), 0.0) + v
        grand = sum(totals.values())
        if grand:
            top = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:3]
            for seg, tot in top:
                insights.append({
                    "kind": "top_contributor",
                    "title": f"Top contributor: {seg} ({tot / grand * 100:.1f}% of total)",
                    "body": f"{seg} contributes {tot:.2f} of {grand:.2f} total.",
                    "confidence": 0.85,
                    "segment": seg,
                })

    # Anomaly.
    out = outlier_iqr_zscore(xs)
    for idx in out["indices"][:5]:
        insights.append({
            "kind": "anomaly",
            "title": f"Anomaly at step {idx} (value {xs[idx]:.2f})",
            "body": f"Point {idx} deviates from the bulk of the series (IQR/z-score).",
            "confidence": 0.8,
            "index": idx,
        })

    # Changepoint: max abs shift between left/right rolling means.
    if len(xs) >= 6:
        best_i, best_shift = -1, 0.0
        for i in range(2, len(xs) - 2):
            left = sum(xs[:i]) / i
            right = sum(xs[i:]) / (len(xs) - i)
            shift = abs(right - left)
            if shift > best_shift:
                best_shift, best_i = shift, i
        base = abs(sum(xs) / len(xs)) or 1.0
        if best_i >= 0 and best_shift > 0.5 * base:
            insights.append({
                "kind": "changepoint",
                "title": f"Possible changepoint at step {best_i}",
                "body": f"Mean shifts by {best_shift:.2f} around index {best_i}.",
                "confidence": 0.7,
                "index": best_i,
            })

    # High correlation.
    if other is not None:
        r = correlation(xs, list(other))
        if r is not None and abs(r) >= 0.7:
            insights.append({
                "kind": "high_correlation",
                "title": f"High correlation with {other_name} (r={r:.2f})",
                "body": f"Pearson r={r:.3f} indicates strong linear association.",
                "confidence": 0.8,
            })

    # Quality issues: flat series or overall trend + pct change summary.
    t = trend(xs)
    overall = pct_change(xs[0], xs[-1])
    if all(v == xs[0] for v in xs):
        insights.append({"kind": "quality_issue", "title": "Flat series", "body": "All values identical; check for stale data.", "confidence": 0.9})
    else:
        insights.append({
            "kind": "trend",
            "title": f"Overall trend {t['direction']} ({(overall or 0):+.1f}% end-to-end)",
            "body": f"Slope {t['slope']:.4f} per step; {xs[0]:.2f} -> {xs[-1]:.2f}.",
            "confidence": 0.75,
        })

    # Unusual segment via cohort deviation.
    if labels and len(labels) == len(series):
        g = mean(xs) or 0.0
        ch = cohort(list(series), list(labels))
        worst, worst_dev = None, 0.0
        for seg, s in ch.items():
            if s["mean"] is None:
                continue
            dev = abs(s["mean"] - g)
            if dev > worst_dev:
                worst, worst_dev = seg, dev
        if worst and worst_dev > 0:
            insights.append({
                "kind": "unusual_segment",
                "title": f"Unusual segment: {worst} (mean {ch[worst]['mean']:.2f} vs global {g:.2f})",
                "body": f"{worst} deviates by {worst_dev:.2f} from the global mean.",
                "confidence": 0.7,
                "segment": worst,
            })

    return insights
