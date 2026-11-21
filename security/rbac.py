"""Workspace isolation + RBAC ownership checks."""
from __future__ import annotations

from fastapi import HTTPException


def assert_workspace_access(user_workspace_id: str, resource_workspace_id: str) -> None:
    """Raise 403 when a resource lives outside the caller's workspace."""
    if user_workspace_id != resource_workspace_id:
        raise HTTPException(status_code=403, detail="Cross-workspace access denied")


def assert_role(user_role: str, required: str) -> None:
    """Raise 403 when the user's role is below the required role."""
    from app.core.security import has_role

    if not has_role(user_role, required):
        raise HTTPException(status_code=403, detail=f"Requires role {required}")


def can_read(role: str) -> bool:
    """All roles can read."""
    return role in ("admin", "analyst", "viewer")


def can_write(role: str) -> bool:
    """Analysts and admins can write."""
    return role in ("admin", "analyst")


def can_admin(role: str) -> bool:
    """Only admins manage users/settings."""
    return role == "admin"
