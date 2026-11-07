"""Request and response contracts for authentication and account settings."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


def _normalize_email(value: object) -> object:
    if isinstance(value, str):
        return value.strip().lower()
    return value


def _normalize_name(value: object) -> object:
    if not isinstance(value, str):
        return value
    name = " ".join(value.split())
    return name or None


class RegisterRequest(_StrictModel):
    email: EmailStr = Field(max_length=320)
    password: str = Field(min_length=12, max_length=128)
    full_name: str | None = Field(default=None, max_length=120)

    _email = field_validator("email", mode="before")(_normalize_email)
    _name = field_validator("full_name", mode="before")(_normalize_name)

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is not None and len(value) < 2:
            raise ValueError("Use at least 2 characters.")
        return value


class LoginRequest(_StrictModel):
    email: EmailStr = Field(max_length=320)
    password: str = Field(min_length=1, max_length=128)

    _email = field_validator("email", mode="before")(_normalize_email)


class ForgotPasswordRequest(_StrictModel):
    email: EmailStr = Field(max_length=320)

    _email = field_validator("email", mode="before")(_normalize_email)


class ResetPasswordRequest(_StrictModel):
    token: str = Field(min_length=20, max_length=512)
    password: str = Field(min_length=12, max_length=128)


class UpdateProfileRequest(_StrictModel):
    full_name: str | None = Field(default=None, max_length=120)
    timezone: str | None = Field(default=None, min_length=1, max_length=64)
    week_starts_on: int | None = Field(default=None, ge=0, le=6)

    _name = field_validator("full_name", mode="before")(_normalize_name)

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is not None and len(value) < 2:
            raise ValueError("Use at least 2 characters.")
        return value


class UserSettingsResponse(BaseModel):
    timezone: str
    week_starts_on: int


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    is_active: bool
    email_verified: bool
    last_login_at: datetime | None
    created_at: datetime
    settings: UserSettingsResponse


class CsrfResponse(BaseModel):
    csrf_token: str


class AuthResponse(BaseModel):
    user: UserResponse
    csrf_token: str


class MessageResponse(BaseModel):
    message: str


class SessionResponse(BaseModel):
    id: uuid.UUID
    created_at: datetime
    last_used_at: datetime | None
    expires_at: datetime
    user_agent: str | None
    ip_address: str | None
    current: bool


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]
