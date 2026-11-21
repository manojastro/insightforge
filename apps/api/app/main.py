"""InsightForge FastAPI application entrypoint."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.observability import ObservabilityMiddleware, configure_logging
from app.routers import analysis, audit_api, auth, datasets, evals, insights, reports

settings = get_settings()
configure_logging(settings.LOG_LEVEL)

app = FastAPI(title="InsightForge API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(ObservabilityMiddleware)

app.include_router(auth.router)
app.include_router(datasets.router)
app.include_router(analysis.router)
app.include_router(insights.router)
app.include_router(reports.router)
app.include_router(evals.router)
app.include_router(audit_api.router)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/readyz")
def readyz() -> dict[str, str]:
    """Readiness probe (checks DB connectivity non-fatally)."""
    try:
        from app.core.deps import get_engine
        from sqlalchemy import text

        eng = get_engine()
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as exc:  # noqa: BLE001
        return {"status": f"degraded: {exc}"}
