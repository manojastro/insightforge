"""Planner + sqlgen tests (deterministic, no network)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.planner import classify_question, generate_plan, revise_plan  # noqa: E402
from agents.sqlgen import generate_sql, generate_sql_with_llm  # noqa: E402


def test_classifier():
    assert classify_question("Show revenue trend over time") == "timeseries"
    assert classify_question("Compare East vs West sales") == "comparison"
    assert classify_question("What correlates with churn? correlation analysis") == "correlation"
    assert classify_question("Find outliers and anomalies") == "outlier"
    assert classify_question("Why did sales drop? root cause drivers") == "root_cause"
    assert classify_question("Total revenue please") == "simple_aggregation"


def test_plan_steps_revisable():
    plan = generate_plan("Compare East vs West sales", available_columns=["region", "sales"])
    assert plan["question_type"] == "comparison"
    assert any(s["step"] == "ground_columns" for s in plan["steps"])
    rev = revise_plan(plan, "exclude test orders")
    assert rev["revision"] == 1 and len(rev["steps"]) == len(plan["steps"]) + 1


def test_sqlgen_safe():
    sql = generate_sql("Total sales by region", "comparison", table="data", columns=["region", "sales"])
    assert "SELECT" in sql.upper() and '"data"' in sql
    assert "region" in sql and "sales" in sql


def test_sqlgen_llm_stub_fallback():
    sql = generate_sql_with_llm("Total sales", "simple_aggregation", "data", ["sales"], llm_call=None)
    assert "SELECT" in sql.upper()
    evil = generate_sql_with_llm("x", "simple_aggregation", "data", ["sales"], llm_call=lambda p: "DROP TABLE data")
    assert "DROP" not in evil.upper()
