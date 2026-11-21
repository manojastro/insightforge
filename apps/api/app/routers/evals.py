"""Evals router: store eval questions and score deterministic checks."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.entities import EvaluationQuestion, EvaluationResult, User
from app.schemas.api import EvalCreate, EvalResultOut

router = APIRouter(prefix="/evals", tags=["evals"])


@router.post("", status_code=201)
def create_eval(body: EvalCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict[str, Any]:
    """Store an evaluation question (details of scoring live in evals/*.json, owned by another agent)."""
    _ = user
    eq = EvaluationQuestion(dataset_id=body.dataset_id, question=body.question, expected_json=body.expected)
    db.add(eq)
    db.commit()
    db.refresh(eq)
    return {"id": eq.id, "question": eq.question}


@router.post("/{eval_id}/run", response_model=EvalResultOut)
def run_eval(eval_id: str, payload: dict[str, Any], db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> EvaluationResult:
    """Score a candidate answer against the stored expectation (exact/contains/numeric-tolerance)."""
    _ = user
    eq = db.query(EvaluationQuestion).filter(EvaluationQuestion.id == eval_id).first()
    if eq is None:
        raise HTTPException(status_code=404, detail="Eval not found")
    expected = eq.expected_json or {}
    actual = payload.get("actual")
    passed, score, details = _score(expected, actual)
    res = EvaluationResult(evaluation_question_id=eq.id, passed=passed, score=score, details_json=details)
    db.add(res)
    db.commit()
    db.refresh(res)
    return res


def _score(expected: dict[str, Any], actual: Any) -> tuple[bool, float, dict[str, Any]]:
    """Deterministic scorer: numeric tolerance, contains, or exact match."""
    mode = str(expected.get("mode", "exact"))
    want = expected.get("value")
    if mode == "numeric":
        try:
            tol = float(expected.get("tolerance", 1e-6))
            diff = abs(float(actual) - float(want))  # type: ignore[arg-type]
            passed = diff <= tol
            return passed, 1.0 if passed else 0.0, {"diff": diff, "tolerance": tol}
        except (TypeError, ValueError):
            return False, 0.0, {"error": "non-numeric actual"}
    if mode == "contains":
        passed = str(want) in str(actual)
        return passed, 1.0 if passed else 0.0, {"want": want}
    passed = actual == want
    return passed, 1.0 if passed else 0.0, {"want": want, "actual": actual}
