"""Profiler tests (no network; temp CSV files only)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analytics.profiler import detect_encoding, profile_file  # noqa: E402


def _csv(tmp_path, content: str) -> str:
    p = tmp_path / "sample.csv"
    p.write_text(content, encoding="utf-8")
    return str(p)


def test_profile_basic(tmp_path):
    path = _csv(tmp_path, "date,region,revenue\n2024-01-01,East,100\n2024-02-01,West,200\n2024-03-01,East,300\n")
    prof = profile_file(path)
    assert prof["row_count"] == 3
    assert prof["column_count"] == 3
    by_name = {c["name"]: c for c in prof["columns"]}
    assert by_name["revenue"]["semantic_type"] == "numeric"
    assert by_name["revenue"]["descriptives"]["mean"] == 200.0
    assert "date" in prof["time_fields"]


def test_profile_duplicates_missing(tmp_path):
    path = _csv(tmp_path, "a,b\n1,x\n1,x\n,2\n")
    prof = profile_file(path)
    assert prof["duplicate_rows"] == 1
    by_name = {c["name"]: c for c in prof["columns"]}
    assert by_name["a"]["missing"] == 1


def test_detect_encoding(tmp_path):
    path = _csv(tmp_path, "a\n1\n")
    assert isinstance(detect_encoding(path), str)


def test_unsupported_extension(tmp_path):
    p = tmp_path / "f.txt"
    p.write_text("hi", encoding="utf-8")
    try:
        profile_file(str(p))
        raise AssertionError("should have raised")
    except ValueError:
        pass
