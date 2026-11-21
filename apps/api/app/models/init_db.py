"""Create all tables (dev / SQLite fallback). For Postgres use Alembic in prod."""
from __future__ import annotations


def init_db(engine) -> None:  # type: ignore[no-untyped-def]
    """Create all tables registered on Base metadata."""
    from .entities import Base

    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    from app.core.deps import get_engine

    init_db(get_engine())
    print("init_db: tables created")
