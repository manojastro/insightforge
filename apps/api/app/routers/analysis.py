"""Analysis router: ask -> plan -> SQL -> execute -> verify."""
from __future__ import annotations

import os
import sys
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.entities import (
    AnalysisPlan,
    AnalysisSession,
    Dataset,
    Query,
    QueryExecution,
    Question,
    Result,
    User,
)
from app.schemas.api import AskRequest, PlanOut, QueryOut, VerifyOut

router = APIRouter(prefix="/analysis", tags=["analysis"])


def _extend_path() -> None:
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
    if root not in sys.path:
        sys.path.insert(0, root)


@router.post("/ask", response_model=PlanOut)
def ask(body: AskRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict[str, Any]:
    """Classify the question, generate a plan + SQL stub, and persist rows."""
    _extend_path()
    from agents.planner import classify_question, generate_plan
    from agents.sqlgen import generate_sql

    session = None
    if body.session_id:
        session = (
            db.query(AnalysisSession)
            .filter(AnalysisSession.id == body.session_id, AnalysisSession.workspace_id == user.workspace_id)
            .first()
        )
    if session is None:
        session = AnalysisSession(workspace_id=user.workspace_id, dataset_id=body.dataset_id, created_by=user.id, title=body.question[:80])
        db.add(session)
        db.flush()
    allowed_columns: list[str] = []
    table_name = "data"
    if body.dataset_id:
        ds = db.query(Dataset).filter(Dataset.id == body.dataset_id, Dataset.workspace_id == user.workspace_id).first()
        if ds is None:
            raise HTTPException(status_code=404, detail="Dataset not found")

    qtype = classify_question(body.question)
    plan = generate_plan(body.question, qtype, available_columns=allowed_columns or None)
    q = Question(session_id=session.id, text=body.question, question_type=qtype)
    db.add(q)
    db.flush()
    ap = AnalysisPlan(question_id=q.id, plan_json=plan, status="ready")
    db.add(ap)
    db.flush()
    sql = generate_sql(body.question, qtype, table=table_name, columns=allowed_columns or None)
    dbq = Query(plan_id=ap.id, sql_text=sql, status="generated")
    db.add(dbq)
    db.commit()
    return {"id": ap.id, "question_id": q.id, "question_type": qtype, "steps": plan.get("steps", []), "sql": sql, "status": ap.status}


@router.post("/execute", response_model=QueryOut)
def execute_sql(payload: dict[str, Any], db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict[str, Any]:
    """Execute read-only SQL in the DuckDB sandbox (table allowlist = dataset tables)."""
    _extend_path()
    from sandbox.duckdb_sandbox import execute_sandbox

    sql = str(payload.get("sql", ""))
    dataset_id = payload.get("dataset_id")
    allowed = ["data"]
    if dataset_id:
        ds = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.workspace_id == user.workspace_id).first()
        if ds is None:
            raise HTTPException(status_code=404, detail="Dataset not found")
    tables = {t: t for t in allowed}
    result = execute_sandbox(sql, tables=tables)
    # Persist execution artifacts minimally.
    q = Query(plan_id=None, sql_text=sql, status="executed")
    db.add(q)
    db.flush()
    ex = QueryExecution(query_id=q.id, status="success", duration_ms=result["duration_ms"], row_count=result["row_count"])
    db.add(ex)
    db.flush()
    db.add(Result(execution_id=ex.id, columns_json=result["columns"], rows_json=result["rows"], row_count=result["row_count"]))
    db.commit()
    return {"columns": result["columns"], "rows": result["rows"], "row_count": result["row_count"], "duration_ms": result["duration_ms"]}


@router.post("/verify", response_model=VerifyOut)
def verify_narrative(payload: dict[str, Any]) -> dict[str, Any]:
    """Verify a narrative against result rows."""
    _extend_path()
    from agents.verifier import verify_narrative as _verify

    narrative = str(payload.get("narrative", ""))
    columns = list(payload.get("columns", []))
    rows = [list(r) for r in payload.get("rows", [])]
    verdict = _verify(narrative, columns, rows)
    return {"passed": verdict.passed, "issues": verdict.issues}
