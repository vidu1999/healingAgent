"""User schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    email: str
    username: str
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    username: str
    is_active: bool
    is_superuser: bool

    model_config = ConfigDict(from_attributes=True)
