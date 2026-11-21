"""Verifier tests (deterministic, no network)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.verifier import verify_narrative  # noqa: E402


def test_pass_numbers_exist():
    v = verify_narrative("Revenue rose from 100 to 150.", ["revenue"], [[100], [150]])
    assert v.passed, v.issues


def test_fail_missing_number():
    v = verify_narrative("Revenue hit 9999.", ["revenue"], [[100], [150]])
    assert not v.passed and any("9999" in i for i in v.issues)


def test_fail_wrong_direction():
    v = verify_narrative("Revenue decreased from 100 to 150.", ["revenue"], [[100], [150]])
    assert not v.passed


def test_pct_derived_ok():
    v = verify_narrative("Growth of 50% from 100 to 150.", ["v"], [[100], [150]])
    assert v.passed, v.issues


def test_chart_mismatch():
    v = verify_narrative("Value 100.", ["v"], [[100]], chart_spec={"x": "nope"})
    assert not v.passed
