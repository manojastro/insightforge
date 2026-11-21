"""Auth router: register, login, me."""
from __future__ import annotations

import re
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models.entities import User, Workspace
from app.schemas.api import LoginRequest, RegisterRequest, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _slug(name: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "ws"
    return f"{base}-{uuid.uuid4().hex[:6]}"


@router.post("/register", response_model=UserOut, status_code=201)
def register(body: RegisterRequest, db: Session = Depends(get_db)) -> User:
    """Create a workspace + user."""
    if not _EMAIL_RE.match(body.email):
        raise HTTPException(status_code=422, detail="Invalid email")
    if body.role not in ("admin", "analyst", "viewer"):
        raise HTTPException(status_code=422, detail="Invalid role")
    ws = Workspace(name=body.workspace_name, slug=_slug(body.workspace_name))
    db.add(ws)
    db.flush()
    if db.query(User).filter(User.workspace_id == ws.id, User.email == body.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(workspace_id=ws.id, email=body.email, password_hash=hash_password(body.password), role=body.role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """Validate credentials and return a JWT."""
    user = db.query(User).filter(User.email == body.email).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(subject=user.id, extra={"ws": user.workspace_id, "role": user.role})
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> User:
    """Return the current user."""
    return user
