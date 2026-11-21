"""Structured logging + observability middleware (request-id, latency, cost stub)."""
from __future__ import annotations

import time
import uuid

import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger("insightforge")


def configure_logging(level: str = "INFO") -> None:
    """Configure structlog with JSON rendering."""
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
    )


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Attach request-id, measure latency, log tokens/cost stub fields."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
        structlog.contextvars.bind_contextvars(request_id=request_id)
        start = time.perf_counter()
        # Stubs populated downstream by LLM-calling routes.
        request.state.tokens_used = 0
        request.state.estimated_cost_usd = 0.0
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000.0
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Duration-Ms"] = f"{duration_ms:.1f}"
        logger.info(
            "http_request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round(duration_ms, 2),
            tokens_used=getattr(request.state, "tokens_used", 0),
            cost_usd=getattr(request.state, "estimated_cost_usd", 0.0),
        )
        structlog.contextvars.unbind_contextvars("request_id")
        return response
