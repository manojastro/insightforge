"""Reports router: assemble a JSON report stub (PDF/minimal handled elsewhere)."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.entities import AnalysisSession, Insight, Question, User
from app.schemas.api import ReportRequest

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("")
def build_report(body: ReportRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict[str, Any]:
    """Assemble questions + insights into a report payload."""
    questions: list[str] = []
    if body.session_id:
        rows = db.query(Question).join(AnalysisSession, Question.session_id == AnalysisSession.id).filter(
            AnalysisSession.id == body.session_id, AnalysisSession.workspace_id == user.workspace_id
        ).all()
        questions = [r.text for r in rows]
    insights = db.query(Insight).filter(Insight.workspace_id == user.workspace_id).order_by(Insight.created_at.desc()).limit(50).all()
    return {
        "format": body.format,
        "session_id": body.session_id,
        "dataset_id": body.dataset_id,
        "questions": questions,
        "insights": [{"title": i.title, "body": i.body, "kind": i.kind} for i in insights],
    }
