"""Auth schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    message: str
    user: dict


class MeResponse(BaseModel):
    id: str
    email: str
    username: str
    is_active: bool
    is_superuser: bool
    roles: list[str] = []

    model_config = ConfigDict(from_attributes=True)


class RefreshResponse(BaseModel):
    message: str


class RoleOut(BaseModel):
    id: str
    name: str
    description: str | None = None

    model_config = ConfigDict(from_attributes=True)
