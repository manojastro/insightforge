"""PII detection + masking (regex heuristics + column flags)."""
from __future__ import annotations

import re
from typing import Any

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)?\d{3}[\s.-]?\d{4}")
CC_RE = re.compile(r"\b(?:\d[ -]?){13,19}\b")
IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
ADDRESS_KW = ("street", "avenue", "road", "address", "zip", "postal", "city", "state")
NAME_COLS = ("first_name", "last_name", "full_name", "name", "customer_name", "employee_name")


def _luhn_ok(digits: str) -> bool:
    ds = [int(d) for d in re.sub(r"\D", "", digits)]
    if len(ds) < 13:
        return False
    total = 0
    for i, d in enumerate(reversed(ds)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def detect_pii_in_values(values: list[Any]) -> list[str]:
    """Scan sample values; return sorted PII type hits."""
    hits: set[str] = set()
    for v in values:
        s = str(v)
        if EMAIL_RE.search(s):
            hits.add("email")
        if SSN_RE.search(s):
            hits.add("ssn")
        if IP_RE.search(s):
            # Validate octets to reduce false positives.
            m = IP_RE.search(s)
            if m and all(0 <= int(p) <= 255 for p in m.group(0).split(".")):
                hits.add("ip")
        if PHONE_RE.search(s) and len(re.sub(r"\D", "", s)) >= 10:
            # Avoid flagging plain integers/years.
            digits = re.sub(r"\D", "", s)
            if not (s.strip().isdigit() and len(s.strip()) <= 6):
                hits.add("phone")
        mcc = CC_RE.search(s)
        if mcc and _luhn_ok(mcc.group(0)):
            hits.add("credit_card")
        low = s.lower()
        if any(k in low for k in ADDRESS_KW):
            hits.add("address")
    return sorted(hits)


def column_pii_flags(column_name: str, samples: list[Any]) -> list[str]:
    """Combine name heuristic with value scan."""
    flags = set(detect_pii_in_values(samples))
    if column_name.lower() in NAME_COLS or "email" in column_name.lower() or "phone" in column_name.lower():
        flags.add("name_heuristic" if "name" in column_name.lower() else column_name.lower())
    return sorted(flags)


def mask_value(value: Any, pii_types: list[str] | None = None) -> str:
    """Mask a single value (email user, phone digits, generic fallback)."""
    s = str(value)
    if EMAIL_RE.search(s):
        return EMAIL_RE.sub(lambda m: "***@" + m.group(0).split("@")[1], s)
    if pii_types and "phone" in pii_types:
        return re.sub(r"\d", "*", s)
    if len(s) <= 4:
        return "*" * len(s)
    return s[:2] + "*" * (len(s) - 4) + s[-2:]


def mask_row(row: dict[str, Any], pii_columns: dict[str, list[str]]) -> dict[str, Any]:
    """Mask PII columns in a row dict."""
    out = dict(row)
    for col, types in pii_columns.items():
        if col in out and out[col] is not None:
            out[col] = mask_value(out[col], types)
    return out


def exclude_pii_columns(columns: list[str], pii_columns: dict[str, list[str]]) -> list[str]:
    """Return columns with PII-flagged ones removed."""
    return [c for c in columns if c not in pii_columns]
