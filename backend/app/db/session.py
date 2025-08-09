"""Initialisation engine SQLAlchemy et session factory.

SQLite: create_all automatique pour dev/tests (Alembic pour prod/PostgreSQL).
"""
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import get_settings
from backend.app.db.base import Base
from backend.app.db.models import *  # noqa: F401,F403 ensure models registered before create_all

settings = get_settings()
if settings.database_url.startswith("sqlite"):
    engine = create_engine(
    settings.database_url,
    echo=settings.debug_sql,
        future=True,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_engine(
        settings.database_url,
    echo=settings.debug_sql,
        future=True,
        pool_pre_ping=settings.pool_pre_ping,
        pool_size=settings.pool_size,
        max_overflow=settings.max_overflow,
        pool_recycle=settings.pool_recycle,
    )

# Slow query logging (dev): log > 0.5s
try:
    from typing import Any

    from loguru import logger

    @event.listens_for(engine, "after_cursor_execute")
    def _log_slow_queries(
        conn: Any, cursor: Any, statement: str, parameters: Any, context: Any, executemany: bool
    ) -> None:
        total = (
            context._query_end_time - context._query_start_time  # type: ignore[attr-defined]
            if hasattr(context, "_query_end_time") and hasattr(context, "_query_start_time")
            else None
        )
        if total and total * 1000 > settings.slow_query_ms:
            logger.warning(f"Slow query {total*1000:.1f}ms: {statement}")

    @event.listens_for(engine, "before_cursor_execute")
    def _before_cursor_execute(
        conn: Any, cursor: Any, statement: str, parameters: Any, context: Any, executemany: bool
    ) -> None:
        import time
        context._query_start_time = time.time()  # type: ignore[attr-defined]

    @event.listens_for(engine, "after_cursor_execute")
    def _after_cursor_execute(
        conn: Any, cursor: Any, statement: str, parameters: Any, context: Any, executemany: bool
    ) -> None:
        import time
        context._query_end_time = time.time()  # type: ignore[attr-defined]
except Exception:
    pass

# Auto-create tables for SQLite (tests/dev)
if settings.database_url.startswith("sqlite"):
    Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, class_=Session)

def get_db() -> Generator[Session, None, None]:
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
