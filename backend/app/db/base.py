"""SQLAlchemy declarative base and shared column helpers."""

from __future__ import annotations

import datetime as dt
import uuid
from typing import Annotated

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# UTC-aware timestamp, default now()
UTCDateTime = Annotated[
    dt.datetime,
    mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    ),
]


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models.

    UUID primary keys (String(36)) are used everywhere so the same models work
    on SQLite (dev fallback) and PostgreSQL (production).
    """

    __abstract__ = True

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def to_dict(self) -> dict:
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
