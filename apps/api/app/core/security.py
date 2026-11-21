"""JWT auth, password hashing, and RBAC helpers."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Role(str, Enum):
    """Workspace roles ordered by privilege (admin > analyst > viewer)."""

    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


_ROLE_RANK = {Role.VIEWER: 0, Role.ANALYST: 1, Role.ADMIN: 2}


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return pwd_context.verify(plain, hashed)


def hash_password(plain: str) -> str:
    """Hash a plaintext password with bcrypt."""
    return pwd_context.hash(plain)


def create_access_token(subject: str, extra: Optional[dict[str, Any]] = None, expires_minutes: Optional[int] = None) -> str:
    """Create a signed JWT access token."""
    settings = get_settings()
    expire_delta = timedelta(minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: dict[str, Any] = {"sub": subject, "exp": datetime.now(timezone.utc) + expire_delta}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT, raising ValueError on failure."""
    settings = get_settings()
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as exc:
        raise ValueError(f"invalid token: {exc}") from exc


def has_role(user_role: str, required: str) -> bool:
    """Return True if user_role meets or exceeds the required role."""
    try:
        return _ROLE_RANK[Role(user_role)] >= _ROLE_RANK[Role(required)]
    except ValueError:
        return False
