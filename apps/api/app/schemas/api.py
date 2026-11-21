"""Pydantic request/response schemas for the InsightForge API."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# --- Auth ---
class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)
    workspace_name: str = "Default"
    role: str = "analyst"


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: str
    email: str
    role: str
    workspace_id: str

    model_config = {"from_attributes": True}


# --- Datasets ---
class DatasetCreate(BaseModel):
    name: str
    description: Optional[str] = None


class DatasetOut(BaseModel):
    id: str
    workspace_id: str
    name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ProfileOut(BaseModel):
    dataset_id: str
    profile: dict[str, Any]


# --- Analysis ---
class AskRequest(BaseModel):
    question: str
    dataset_id: Optional[str] = None
    session_id: Optional[str] = None


class PlanStep(BaseModel):
    step: str
    detail: Optional[str] = None


class PlanOut(BaseModel):
    id: str
    question_id: str
    question_type: str
    steps: list[dict[str, Any]]
    sql: Optional[str] = None
    status: str = "draft"


class QueryOut(BaseModel):
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    duration_ms: float


class VerifyOut(BaseModel):
    passed: bool
    issues: list[str]


# --- Insights / reports ---
class InsightOut(BaseModel):
    id: str
    kind: str
    title: str
    body: Optional[str] = None
    confidence: Optional[float] = None

    model_config = {"from_attributes": True}


class ReportRequest(BaseModel):
    session_id: Optional[str] = None
    dataset_id: Optional[str] = None
    format: str = "json"


# --- Evals ---
class EvalCreate(BaseModel):
    dataset_id: Optional[str] = None
    question: str
    expected: Optional[dict[str, Any]] = None


class EvalResultOut(BaseModel):
    id: str
    passed: bool
    score: Optional[float] = None
    details: Optional[dict[str, Any]] = None


# --- Audit ---
class AuditOut(BaseModel):
    id: str
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
