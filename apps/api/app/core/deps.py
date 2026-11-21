"""FastAPI dependencies: DB session, current user, workspace scoping."""
from __future__ import annotations

from typing import Generator, Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .config import get_settings
from .security import decode_token

_engine = None
_SessionLocal = None


def get_engine():  # type: ignore[no-untyped-def]
    """Lazily create the SQLAlchemy engine (Postgres with SQLite fallback)."""
    global _engine, _SessionLocal
    if _engine is None:
        settings = get_settings()
        url = settings.DATABASE_URL
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        _engine = create_engine(url, pool_pre_ping=True, connect_args=connect_args)
        _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
    return _engine


def get_db() -> Generator[Session, None, None]:
    """Yield a DB session per request."""
    get_engine()
    assert _SessionLocal is not None
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user_id(authorization: Optional[str] = Header(default=None)) -> str:
    """Extract user id (sub) from a Bearer JWT; 401 on failure."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_token(token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")
    return str(sub)


def get_current_user(db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):  # type: ignore[no-untyped-def]
    """Load the current User row."""
    from app.models.entities import User

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
