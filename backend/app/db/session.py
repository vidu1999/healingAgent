"""Database engine and session factory.

Sync SQLAlchemy session is used so the same code path runs on SQLite (dev
fallback) and PostgreSQL (production). FastAPI sync endpoints run in the
threadpool; async adapters (Ollama/GitHub) use their own transport clients.
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.base import Base

_engine = None
_SessionLocal = None


def engine():
    global _engine
    if _engine is None:
        connect_args = {}
        if settings.DATABASE_URL.startswith("sqlite"):
            connect_args["check_same_thread"] = False
            connect_args["timeout"] = 30
        _engine = create_engine(
            settings.DATABASE_URL,
            connect_args=connect_args,
            pool_pre_ping=True,
        )
    return _engine


def session_factory() -> sessionmaker:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=engine(), autoflush=False, autocommit=False, class_=Session
        )
    return _SessionLocal


def get_db():
    """Yield a transactional SQLAlchemy session (FastAPI dependency)."""
    db = session_factory()()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db() -> None:
    """Create all tables. Used only in dev/demo; Alembic is the source of truth."""
    Base.metadata.create_all(bind=engine())
