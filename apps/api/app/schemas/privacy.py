"""Request and response schemas for privacy, consent, export, and deletion (Phase 6)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AIConsentCreate(_StrictModel):
    provider: str = Field(min_length=1, max_length=32)
    policy_version: str = Field(default="1.0", max_length=32)


class AIConsentUpdate(_StrictModel):
    granted: bool
    policy_version: str | None = Field(default=None, max_length=32)


class AIConsentResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    provider: str
    granted_at: datetime | None
    revoked_at: datetime | None
    policy_version: str

    model_config = ConfigDict(from_attributes=True)


class DataExportCreate(_StrictModel):
    pass


class DataExportResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    status: str
    file_path: str | None
    file_size_bytes: int | None
    record_count: int | None
    completed_at: datetime | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AccountDeletionCreate(_StrictModel):
    reason: str | None = Field(default=None, max_length=1000)


class AccountDeletionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    status: str
    confirmation_token: str | None
    confirmed_at: datetime | None
    completed_at: datetime | None
    reason: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditEventResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID | None
    event_type: str
    details: str | None
    ip_address: str | None
    user_agent: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExportDownloadResponse(BaseModel):
    download_url: str
    expires_at: datetime
