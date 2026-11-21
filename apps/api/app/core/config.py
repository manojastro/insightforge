"""Application configuration via environment variables."""
from __future__ import annotations

import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central typed settings object."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"
    DATABASE_URL: str = "sqlite:///./insightforge.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    JWT_SECRET_KEY: str = "change-me-dev-secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    UPLOAD_DIR: str = "./data/uploads"
    MAX_UPLOAD_MB: int = 200
    SANDBOX_ROW_LIMIT: int = 5000
    SANDBOX_TIMEOUT_S: int = 15

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse comma-separated CORS origins."""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_sqlite(self) -> bool:
        """True when the configured DATABASE_URL is SQLite (local fallback)."""
        return self.DATABASE_URL.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor (override DATABASE_URL from env at runtime)."""
    # Allow plain DATABASE_URL env var to win even without .env reload.
    override = os.getenv("DATABASE_URL")
    if override:
        return Settings(DATABASE_URL=override)
    return Settings()
