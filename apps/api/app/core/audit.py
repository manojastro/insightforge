"""Audit event helper — persists audit rows without failing the request."""
from __future__ import annotations

from typing import Any, Optional

import structlog

logger = structlog.get_logger("insightforge.audit")


def build_audit_payload(
    workspace_id: Optional[str],
    actor_id: Optional[str],
    action: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    payload: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Build a dict matching the AuditEvent model fields."""
    return {
        "workspace_id": workspace_id,
        "actor_id": actor_id,
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "payload": payload or {},
    }


def record_audit(db_session: Any, **kwargs: Any) -> None:
    """Insert an AuditEvent row; never raises (logs on failure)."""
    try:
        from app.models.entities import AuditEvent  # local import to avoid cycles

        event = AuditEvent(**build_audit_payload(**kwargs))  # type: ignore[arg-type]
        db_session.add(event)
        db_session.commit()
    except Exception as exc:  # noqa: BLE001 — audit must not break requests
        logger.warning("audit_write_failed", error=str(exc))
        try:
            db_session.rollback()
        except Exception:
            pass
