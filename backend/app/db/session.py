"""Initialisation engine SQLAlchemy et session factory.

SQLite: create_all automatique pour dev/tests (Alembic pour prod/PostgreSQL).
"""
from sqlalchemy import create_engine
from typing import Generator
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import get_settings
from backend.app.db.base import Base
from backend.app.db.models import *  # noqa: F401,F403 ensure models registered before create_all

settings = get_settings()
engine = create_engine(
    settings.database_url,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)

# Auto-create tables for SQLite (tests/dev). For PostgreSQL rely on Alembic migrations.
if settings.database_url.startswith("sqlite"):
    Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, class_=Session)

def get_db() -> Generator[Session, None, None]:
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
