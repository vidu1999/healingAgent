"""GitHub schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RepositoryRegister(BaseModel):
    full_name: str  # owner/name
    clone_url: str | None = None
    allow_write: bool = False


class WebhookDelivery(BaseModel):
    delivery_id: str
    event: str
    signature: str | None = None
    payload: dict

    model_config = ConfigDict(from_attributes=True)
