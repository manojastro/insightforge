"""Narrative verifier: every number/claim in prose must trace to result rows.

Checks:
- numbers in narrative exist in results (numeric tolerance)
- percent values are arithmetically correct vs the referenced pair
- direction words (increase/decrease) match the sign of change
- periods/labels mentioned exist in results
- chart spec matches result columns
- no unsupported superlatives without evidence
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_NUMBER_RE = re.compile(r"-?\d[\d,]*\.?\d*\s?%?")
_PCT_RE = re.compile(r"(-?\d[\d,]*\.?\d*)\s*%")
_INCREASE_RE = re.compile(r"\b(increas\w*|rose|grew|growth|up)\b", re.I)
_DECREASE_RE = re.compile(r"\b(decreas\w*|fell|declin\w*|dropped|down)\b", re.I)
_SUPERLATIVE_RE = re.compile(r"\b(largest|highest|lowest|best|worst|record|all-time)\b", re.I)


@dataclass
class Verdict:
    passed: bool
    issues: list[str] = field(default_factory=list)


def _numbers_in_text(text: str) -> list[float]:
    out = []
    for m in _NUMBER_RE.finditer(text):
        tok = m.group(0).strip().rstrip("%").replace(",", "")
        try:
            out.append(float(tok))
        except ValueError:
            continue
    return out


def _result_numbers(columns: list[str], rows: list[list[Any]]) -> list[float]:
    out = []
    for r in rows:
        for v in r:
            try:
                f = float(v)  # type: ignore[arg-type]
                out.append(f)
            except (TypeError, ValueError):
                continue
    return out


def verify_narrative(
    narrative: str,
    columns: list[str],
    rows: list[list[Any]],
    chart_spec: dict[str, Any] | None = None,
    pct_tolerance: float = 0.6,
    num_tolerance: float = 1e-6,
) -> Verdict:
    """Verify narrative claims against result data."""
    issues: list[str] = []
    if not narrative.strip():
        return Verdict(passed=False, issues=["empty narrative"])
    if not rows:
        return Verdict(passed=False, issues=["no result rows to verify against"])

    res_nums = _result_numbers(columns, rows)
    narr_nums = _numbers_in_text(narrative)

    # 1. Every narrative number must appear (or be derivable as pct/delta).
    for n in narr_nums:
        is_pct_token = f"{n:g}%" in narrative.replace(" ", "") or f"{n}%" in narrative
        if any(abs(n - r) <= max(num_tolerance, abs(r) * 1e-9) for r in res_nums):
            continue
        # Allow percent-change values derived from a pair in results.
        derived = False
        for i in range(len(res_nums)):
            for j in range(len(res_nums)):
                if res_nums[i] == 0:
                    continue
                pct = (res_nums[j] - res_nums[i]) / abs(res_nums[i]) * 100.0
                if abs(pct - n) <= pct_tolerance:
                    derived = True
                    break
            if derived:
                break
        # Allow deltas.
        if not derived:
            for i in range(len(res_nums)):
                for j in range(len(res_nums)):
                    if abs((res_nums[j] - res_nums[i]) - n) <= num_tolerance:
                        derived = True
                        break
                if derived:
                    break
        if not derived:
            issues.append(f"number {n:g} not found in results")

    # 2. Percent correctness: each % in text must match some pair's pct change (or a share).
    total = sum(v for v in res_nums)
    for m in _PCT_RE.finditer(narrative):
        p = float(m.group(1).replace(",", ""))
        ok = False
        for i in range(len(res_nums)):
            for j in range(len(res_nums)):
                if res_nums[i] == 0:
                    continue
                if abs((res_nums[j] - res_nums[i]) / abs(res_nums[i]) * 100.0 - p) <= pct_tolerance:
                    ok = True
                    break
            if ok:
                break
        if not ok and total:
            for v in res_nums:
                if abs(v / total * 100.0 - p) <= pct_tolerance:
                    ok = True
                    break
        if not ok:
            issues.append(f"percent {p:g}% not derivable from results")

    # 3. Direction words must match overall first->last numeric movement.
    if res_nums and len(res_nums) >= 2:
        overall = res_nums[-1] - res_nums[0]
        if _INCREASE_RE.search(narrative) and overall < 0:
            issues.append("claims increase but results decrease overall")
        if _DECREASE_RE.search(narrative) and overall > 0:
            issues.append("claims decrease but results increase overall")

    # 4. Periods/labels: quoted or capitalised tokens should appear in string cells.
    str_cells = {str(v) for r in rows for v in r if isinstance(v, str)}
    if str_cells:
        for tok in set(re.findall(r"[A-Za-z][A-Za-z\-]{2,}", narrative)):
            if tok.lower() in {"the", "and", "with", "from", "total", "value", "period"}:
                continue
            # Only flag tokens that look like proper labels (capitalised) and are absent.
            if tok[0].isupper() and tok not in str_cells and tok.lower() not in {c.lower() for c in str_cells}:
                issues.append(f"label '{tok}' not found in results")
                break  # one is enough to signal; avoid noise

    # 5. Chart matches result.
    if chart_spec:
        for key in ("x", "y", "value", "column"):
            if key in chart_spec and chart_spec[key] not in columns:
                issues.append(f"chart field '{chart_spec[key]}' not in result columns")

    # 6. Superlatives need max/min evidence.
    if _SUPERLATIVE_RE.search(narrative) and res_nums:
        # Require that at least one narrative number equals an extremum.
        extremes = {min(res_nums), max(res_nums)}
        if narr_nums and not any(any(abs(n - e) <= num_tolerance for e in extremes) for n in narr_nums):
            issues.append("superlative used without citing an extreme value from results")

    return Verdict(passed=not issues, issues=issues)
