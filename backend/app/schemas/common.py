"""Common reusable schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int


class Message(BaseModel):
    detail: str


class TimestampMixin(BaseModel):
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UUIDMixin(BaseModel):
    id: UUID

    model_config = ConfigDict(from_attributes=True)
