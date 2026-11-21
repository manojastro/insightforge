"""Explicit agent state machine: understand->plan->generate->validate->execute->inspect->additional->visualize->verify->present.

LangGraph-optional: if `langgraph` is installed and use_langgraph=True, the
same states run as a StateGraph; otherwise a pure-Python loop runs (default).
Every transition appends an audit event dict.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional

STATES = (
    "understand",
    "plan",
    "generate",
    "validate",
    "execute",
    "inspect",
    "additional",
    "visualize",
    "verify",
    "present",
)


class State(str, Enum):
    UNDERSTAND = "understand"
    PLAN = "plan"
    GENERATE = "generate"
    VALIDATE = "validate"
    EXECUTE = "execute"
    INSPECT = "inspect"
    ADDITIONAL = "additional"
    VISUALIZE = "visualize"
    VERIFY = "verify"
    PRESENT = "present"
    DONE = "done"
    FAILED = "failed"


@dataclass
class OrchestratorContext:
    question: str
    table: str = "data"
    columns: list[str] = field(default_factory=list)
    question_type: str = "simple_aggregation"
    plan: dict[str, Any] = field(default_factory=dict)
    sql: str = ""
    result: dict[str, Any] = field(default_factory=dict)
    insights: list[dict[str, Any]] = field(default_factory=list)
    narrative: str = ""
    verdict: dict[str, Any] = field(default_factory=dict)
    audit: list[dict[str, Any]] = field(default_factory=list)
    error: str = ""


def _audit(ctx: OrchestratorContext, state: str, detail: str = "") -> None:
    ctx.audit.append({"state": state, "detail": detail[:500]})


def run_orchestrator(
    question: str,
    table: str = "data",
    columns: list[str] | None = None,
    execute_fn: Optional[Callable[[str], dict[str, Any]]] = None,
    use_langgraph: bool = False,
) -> OrchestratorContext:
    """Run the full pipeline; execute_fn(sql) -> {columns, rows, ...} injectable for tests."""
    ctx = OrchestratorContext(question=question, table=table, columns=columns or [])
    if use_langgraph:
        try:
            return _run_langgraph(ctx, execute_fn)
        except ImportError:
            pass  # fall back to pure python
    return _run_python(ctx, execute_fn)


def _run_python(ctx: OrchestratorContext, execute_fn: Optional[Callable[[str], dict[str, Any]]]) -> OrchestratorContext:
    from agents.planner import classify_question, generate_plan
    from agents.sqlgen import generate_sql
    from agents.verifier import verify_narrative
    from analytics.auto_insights import generate_insights

    # understand
    _audit(ctx, "understand", ctx.question)
    ctx.question_type = classify_question(ctx.question)

    # plan
    _audit(ctx, "plan", ctx.question_type)
    ctx.plan = generate_plan(ctx.question, ctx.question_type, available_columns=ctx.columns or None)

    # generate
    ctx.sql = generate_sql(ctx.question, ctx.question_type, table=ctx.table, columns=ctx.columns or None)
    _audit(ctx, "generate", ctx.sql)

    # validate (sandbox parse gate)
    try:
        import os
        import sys

        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from sandbox.duckdb_sandbox import validate_sql

        validate_sql(ctx.sql, allowed_tables=[ctx.table])
        _audit(ctx, "validate", "ok")
    except Exception as exc:  # noqa: BLE001
        ctx.error = f"validation failed: {exc}"
        _audit(ctx, "validate", ctx.error)
        return ctx

    # execute
    try:
        if execute_fn is None:
            from sandbox.duckdb_sandbox import execute_sandbox

            ctx.result = execute_sandbox(ctx.sql, tables={ctx.table: ctx.table})
        else:
            ctx.result = execute_fn(ctx.sql)
        _audit(ctx, "execute", f"rows={ctx.result.get('row_count')}")
    except Exception as exc:  # noqa: BLE001
        ctx.error = f"execution failed: {exc}"
        _audit(ctx, "execute", ctx.error)
        return ctx

    # inspect: basic shape + numeric series extraction
    rows = ctx.result.get("rows", [])
    cols = ctx.result.get("columns", [])
    _audit(ctx, "inspect", f"cols={cols} n={len(rows)}")

    # additional: derive insights from first numeric column
    series: list[float] = []
    if rows and cols:
        # find first numeric-ish column
        idx = 0
        for j in range(len(cols)):
            try:
                float(rows[0][j])  # type: ignore[arg-type]
                idx = j
                break
            except (TypeError, ValueError, IndexError):
                continue
        for r in rows:
            try:
                series.append(float(r[idx]))
            except (TypeError, ValueError, IndexError):
                continue
    ctx.insights = generate_insights(series) if series else []
    _audit(ctx, "additional", f"insights={len(ctx.insights)}")

    # visualize: pick chart type from question type + shape
    chart_type = "line" if ctx.question_type == "timeseries" else ("bar" if rows else "table")
    ctx.result["chart"] = {"type": chart_type, "x": cols[0] if cols else None}
    _audit(ctx, "visualize", chart_type)

    # verify + present
    if series:
        ctx.narrative = f"Query returned {len(rows)} rows; value moves from {series[0]:.2f} to {series[-1]:.2f}."
    else:
        ctx.narrative = f"Query returned {len(rows)} rows."
    verdict = verify_narrative(ctx.narrative, cols, rows, chart_spec=None)
    ctx.verdict = {"passed": verdict.passed, "issues": verdict.issues}
    _audit(ctx, "verify", f"passed={verdict.passed}")
    _audit(ctx, "present", ctx.narrative)
    return ctx


def _run_langgraph(ctx: OrchestratorContext, execute_fn: Optional[Callable[[str], dict[str, Any]]]) -> OrchestratorContext:
    """Run states as a LangGraph StateGraph (requires `langgraph` installed)."""
    from langgraph.graph import StateGraph  # type: ignore

    def _step(state: dict[str, Any]) -> dict[str, Any]:
        # Delegate the whole python pipeline for one node to keep parity.
        done = _run_python(ctx, execute_fn)
        return {"done": True, "audit_len": len(done.audit)}

    g = StateGraph(dict)
    g.add_node("pipeline", _step)
    g.set_entry_point("pipeline")
    g.set_finish_point("pipeline")
    compiled = g.compile()
    compiled.invoke({})
    return ctx
