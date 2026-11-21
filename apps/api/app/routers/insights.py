"""Insights router: deterministic auto-insights + stored insights."""
from __future__ import annotations

import os
import sys
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.entities import Insight, User

router = APIRouter(prefix="/insights", tags=["insights"])


@router.post("/auto")
def auto_insights(payload: dict[str, Any], db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict[str, Any]:
    """Generate deterministic insights from a numeric series payload."""
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
    if root not in sys.path:
        sys.path.insert(0, root)
    from analytics.auto_insights import generate_insights

    series = payload.get("series", [])
    labels = payload.get("labels")
    dataset_id = payload.get("dataset_id")
    insights = generate_insights(series, labels=labels)
    out = []
    for ins in insights:
        row = Insight(
            workspace_id=user.workspace_id,
            dataset_id=dataset_id,
            kind=ins.get("kind", "generic"),
            title=ins.get("title", ""),
            body=ins.get("body", ""),
            confidence=float(ins.get("confidence", 0.5)),
        )
        db.add(row)
        out.append(ins)
    db.commit()
    return {"insights": out}


@router.get("", response_model=list[dict[str, Any]])
def list_insights(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[dict[str, Any]]:
    """List stored insights for the workspace."""
    rows = db.query(Insight).filter(Insight.workspace_id == user.workspace_id).order_by(Insight.created_at.desc()).limit(100).all()
    return [{"id": r.id, "kind": r.kind, "title": r.title, "body": r.body, "confidence": r.confidence} for r in rows]
