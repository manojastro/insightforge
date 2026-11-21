"""SQLAlchemy entity models for InsightForge.

Covers workspaces, users, datasets + versions, tables/columns/profiles,
analysis sessions/questions/plans/queries/executions/results/charts,
insights/citations, audit events, and evaluation tables.
"""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class _TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Workspace(Base, _TimestampMixin):
    __tablename__ = "workspaces"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="workspace", cascade="all, delete-orphan")
    datasets: Mapped[list["Dataset"]] = relationship(back_populates="workspace", cascade="all, delete-orphan")


class User(Base, _TimestampMixin):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="analyst", nullable=False)

    workspace: Mapped[Workspace] = relationship(back_populates="users")


class Dataset(Base, _TimestampMixin):
    __tablename__ = "datasets"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    workspace: Mapped[Workspace] = relationship(back_populates="datasets")
    versions: Mapped[list["DatasetVersion"]] = relationship(back_populates="dataset", cascade="all, delete-orphan")
    tables: Mapped[list["Table"]] = relationship(back_populates="dataset", cascade="all, delete-orphan")


class DatasetVersion(Base, _TimestampMixin):
    __tablename__ = "dataset_versions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    file_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    file_format: Mapped[str | None] = mapped_column(String(20), nullable=True)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    profile_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    dataset: Mapped[Dataset] = relationship(back_populates="versions")


class Table(Base, _TimestampMixin):
    __tablename__ = "tables"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    dataset_id: Mapped[str] = mapped_column(ForeignKey("datasets.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    dataset: Mapped[Dataset] = relationship(back_populates="tables")
    columns: Mapped[list["Column"]] = relationship(back_populates="table", cascade="all, delete-orphan")
    profiles: Mapped[list["Profile"]] = relationship(back_populates="table", cascade="all, delete-orphan")


class Column(Base, _TimestampMixin):
    __tablename__ = "columns"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    table_id: Mapped[str] = mapped_column(ForeignKey("tables.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    dtype: Mapped[str] = mapped_column(String(60), nullable=False, default="string")
    semantic_type: Mapped[str | None] = mapped_column(String(60), nullable=True)
    nullable: Mapped[bool] = mapped_column(Boolean, default=True)
    is_pii: Mapped[bool] = mapped_column(Boolean, default=False)
    stats_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    table: Mapped[Table] = relationship(back_populates="columns")


class Profile(Base, _TimestampMixin):
    __tablename__ = "profiles"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    table_id: Mapped[str] = mapped_column(ForeignKey("tables.id"), nullable=False)
    profile_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    table: Mapped[Table] = relationship(back_populates="profiles")


class AnalysisSession(Base, _TimestampMixin):
    __tablename__ = "analysis_sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    dataset_id: Mapped[str | None] = mapped_column(ForeignKey("datasets.id"), nullable=True)
    created_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(300), default="Untitled session")

    questions: Mapped[list["Question"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class Question(Base, _TimestampMixin):
    __tablename__ = "questions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    session_id: Mapped[str] = mapped_column(ForeignKey("analysis_sessions.id"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[str | None] = mapped_column(String(60), nullable=True)

    session: Mapped[AnalysisSession] = relationship(back_populates="questions")
    plans: Mapped[list["AnalysisPlan"]] = relationship(back_populates="question", cascade="all, delete-orphan")


class AnalysisPlan(Base, _TimestampMixin):
    __tablename__ = "analysis_plans"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"), nullable=False)
    plan_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="draft", nullable=False)

    question: Mapped[Question] = relationship(back_populates="plans")
    queries: Mapped[list["Query"]] = relationship(back_populates="plan", cascade="all, delete-orphan")


class Query(Base, _TimestampMixin):
    __tablename__ = "queries"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    plan_id: Mapped[str | None] = mapped_column(ForeignKey("analysis_plans.id"), nullable=True)
    sql_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)

    plan: Mapped[AnalysisPlan | None] = relationship(back_populates="queries")
    executions: Mapped[list["QueryExecution"]] = relationship(back_populates="query", cascade="all, delete-orphan")


class QueryExecution(Base, _TimestampMixin):
    __tablename__ = "query_executions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    query_id: Mapped[str] = mapped_column(ForeignKey("queries.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="success", nullable=False)
    duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    query: Mapped[Query] = relationship(back_populates="executions")
    results: Mapped[list["Result"]] = relationship(back_populates="execution", cascade="all, delete-orphan")


class Result(Base, _TimestampMixin):
    __tablename__ = "results"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    execution_id: Mapped[str] = mapped_column(ForeignKey("query_executions.id"), nullable=False)
    columns_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    rows_json: Mapped[list | None] = mapped_column(JSON, nullable=True)
    row_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    execution: Mapped[QueryExecution] = relationship(back_populates="results")
    charts: Mapped[list["Chart"]] = relationship(back_populates="result", cascade="all, delete-orphan")


class Chart(Base, _TimestampMixin):
    __tablename__ = "charts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    result_id: Mapped[str] = mapped_column(ForeignKey("results.id"), nullable=False)
    chart_type: Mapped[str] = mapped_column(String(40), nullable=False, default="bar")
    spec_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    result: Mapped[Result] = relationship(back_populates="charts")


class Insight(Base, _TimestampMixin):
    __tablename__ = "insights"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    dataset_id: Mapped[str | None] = mapped_column(ForeignKey("datasets.id"), nullable=True)
    kind: Mapped[str] = mapped_column(String(60), nullable=False, default="generic")
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    citations: Mapped[list["Citation"]] = relationship(back_populates="insight", cascade="all, delete-orphan")


class Citation(Base, _TimestampMixin):
    __tablename__ = "citations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    insight_id: Mapped[str] = mapped_column(ForeignKey("insights.id"), nullable=False)
    result_id: Mapped[str | None] = mapped_column(ForeignKey("results.id"), nullable=True)
    quote: Mapped[str | None] = mapped_column(Text, nullable=True)
    locator_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    insight: Mapped[Insight] = relationship(back_populates="citations")


class AuditEvent(Base, _TimestampMixin):
    __tablename__ = "audit_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    workspace_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    actor_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True, default=dict)


class EvaluationQuestion(Base, _TimestampMixin):
    __tablename__ = "evaluation_questions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    dataset_id: Mapped[str | None] = mapped_column(ForeignKey("datasets.id"), nullable=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    expected_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    results: Mapped[list["EvaluationResult"]] = relationship(back_populates="eval_question", cascade="all, delete-orphan")


class EvaluationResult(Base, _TimestampMixin):
    __tablename__ = "evaluation_results"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    evaluation_question_id: Mapped[str] = mapped_column(ForeignKey("evaluation_questions.id"), nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    details_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    eval_question: Mapped[EvaluationQuestion] = relationship(back_populates="results")
