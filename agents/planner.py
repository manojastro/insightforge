"""Question classifier + structured plan generator (deterministic, revisable).

Types: simple_aggregation / comparison / timeseries / segmentation /
correlation / outlier / root_cause / statistical / multi_step
"""
from __future__ import annotations

import re
from typing import Any

QUESTION_TYPES = (
    "simple_aggregation",
    "comparison",
    "timeseries",
    "segmentation",
    "correlation",
    "outlier",
    "root_cause",
    "statistical",
    "multi_step",
)

_PATTERNS: list[tuple[str, list[str]]] = [
    ("timeseries", [r"\bover time\b", r"\btrend\b", r"\bmonthly\b", r"\bweekly\b", r"\bdaily\b", r"\btime series\b", r"\bgrowth\b"]),
    ("comparison", [r"\bvs\.?\b", r"\bversus\b", r"\bcompare\b", r"\bdifference between\b", r"\bby region\b", r"\bby category\b"]),
    ("segmentation", [r"\bby segment\b", r"\bper segment\b", r"\bbreak down\b", r"\bbreakdown\b", r"\bcohort\b", r"\bgroup by\b"]),
    ("correlation", [r"\bcorrelat", r"\brelationship between\b", r"\bassociated with\b"]),
    ("outlier", [r"\boutlier\b", r"\banomal", r"\bunusual\b", r"\bspike\b"]),
    ("root_cause", [r"\bwhy\b", r"\broot cause\b", r"\bdriver\b", r"\bexplain\b"]),
    ("statistical", [r"\baverage\b", r"\bmean\b", r"\bmedian\b", r"\bstd\b", r"\bdistribution\b", r"\bpercentile\b", r"\bregression\b", r"\bconfidence\b"]),
    ("simple_aggregation", [r"\btotal\b", r"\bsum\b", r"\bcount\b", r"\bhow many\b", r"\bmax\b", r"\bmin\b"]),
]


def classify_question(question: str) -> str:
    """Rule-based classifier returning one of QUESTION_TYPES."""
    q = question.lower()
    # multi_step when multiple interrogatives / conjunctions join clauses.
    if len(re.findall(r"\?", q)) > 1 or len(re.findall(r"\band\b|\bthen\b|\balso\b", q)) >= 2:
        # Only claim multi_step if it also matches another analytic intent.
        for _t, pats in _PATTERNS:
            if any(re.search(p, q) for p in pats):
                return "multi_step"
    scores: dict[str, int] = {}
    for t, pats in _PATTERNS:
        scores[t] = sum(1 for p in pats if re.search(p, q))
    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] > 0 else "simple_aggregation"


_STEP_TEMPLATES: dict[str, list[dict[str, str]]] = {
    "simple_aggregation": [
        {"step": "identify_metric", "detail": "Extract the metric and aggregation from the question."},
        {"step": "generate_sql", "detail": "Build a single aggregate query."},
        {"step": "execute_validate", "detail": "Run in sandbox and sanity-check row counts."},
    ],
    "comparison": [
        {"step": "identify_groups", "detail": "Find the entities being compared."},
        {"step": "generate_sql", "detail": "Aggregate per group in one query."},
        {"step": "compute_deltas", "detail": "Compute absolute and percent differences."},
        {"step": "execute_validate", "detail": "Run and verify group coverage."},
    ],
    "timeseries": [
        {"step": "identify_time_grain", "detail": "Detect date column and grain (day/week/month)."},
        {"step": "generate_sql", "detail": "Aggregate metric by time bucket."},
        {"step": "compute_trend", "detail": "Slope, pct change, rolling average."},
        {"step": "execute_validate", "detail": "Check continuity of periods."},
    ],
    "segmentation": [
        {"step": "identify_segments", "detail": "Extract segment dimension."},
        {"step": "generate_sql", "detail": "Aggregate metric per segment."},
        {"step": "rank_segments", "detail": "Share of total and top-k."},
    ],
    "correlation": [
        {"step": "identify_pair", "detail": "Extract the two numeric fields."},
        {"step": "generate_sql", "detail": "Select paired non-null observations."},
        {"step": "compute_correlation", "detail": "Pearson r + scatter-ready output."},
    ],
    "outlier": [
        {"step": "identify_metric", "detail": "Extract metric to scan."},
        {"step": "generate_sql", "detail": "Fetch ordered observations."},
        {"step": "detect_outliers", "detail": "IQR + z-score scan."},
    ],
    "root_cause": [
        {"step": "frame_event", "detail": "Isolate the anomalous slice."},
        {"step": "generate_sql", "detail": "Compare slice vs baseline by segments."},
        {"step": "attribute", "detail": "Rank contributing segments."},
    ],
    "statistical": [
        {"step": "identify_test", "detail": "Map question to descriptive/inferential stat."},
        {"step": "generate_sql", "detail": "Pull the needed sample."},
        {"step": "compute_stats", "detail": "quantiles/regression/confidence as needed."},
    ],
    "multi_step": [
        {"step": "decompose", "detail": "Split into sub-questions."},
        {"step": "generate_sql", "detail": "One query per sub-question."},
        {"step": "synthesize", "detail": "Join partial answers into final narrative."},
    ],
}


def generate_plan(question: str, question_type: str | None = None, available_columns: list[str] | None = None) -> dict[str, Any]:
    """Build a structured, revisable plan dict and store-ready payload."""
    qtype = question_type or classify_question(question)
    if qtype not in QUESTION_TYPES:
        qtype = "simple_aggregation"
    steps = [dict(s) for s in _STEP_TEMPLATES[qtype]]
    if available_columns:
        steps.insert(0, {"step": "ground_columns", "detail": f"Allowed columns: {', '.join(available_columns[:20])}"})
    return {
        "question": question,
        "question_type": qtype,
        "steps": steps,
        "revision": 0,
        "status": "draft",
    }


def revise_plan(plan: dict[str, Any], feedback: str) -> dict[str, Any]:
    """Return a new plan revision with feedback appended as a constraint step."""
    out = dict(plan)
    out["steps"] = list(plan.get("steps", [])) + [{"step": "apply_feedback", "detail": feedback[:500]}]
    out["revision"] = int(plan.get("revision", 0)) + 1
    out["status"] = "revised"
    return out
