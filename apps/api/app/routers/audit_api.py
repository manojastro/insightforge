"""Audit router: read-only listing of audit events for the workspace."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.models.entities import AuditEvent, User
from app.schemas.api import AuditOut

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("", response_model=list[AuditOut])
def list_events(limit: int = 100, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[AuditEvent]:
    """List recent audit events scoped to the caller's workspace."""
    limit = max(1, min(limit, 500))
    return (
        db.query(AuditEvent)
        .filter((AuditEvent.workspace_id == user.workspace_id) | (AuditEvent.workspace_id.is_(None)))
        .order_by(AuditEvent.created_at.desc())
        .limit(limit)
        .all()
    )
