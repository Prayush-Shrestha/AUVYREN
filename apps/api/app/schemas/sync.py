"""Request and response contracts for device sync."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SyncDeviceRegisterRequest(_StrictModel):
    device_id: str = Field(min_length=1, max_length=255)
    device_name: str | None = Field(default=None, max_length=255)
    platform: str | None = Field(default=None, max_length=32)
    app_version: str | None = Field(default=None, max_length=64)


class SyncDeviceResponse(_StrictModel):
    id: uuid.UUID
    device_id: str
    device_name: str | None
    platform: str | None
    app_version: str | None
    last_seen_at: datetime | None
    created_at: datetime
    updated_at: datetime


class SyncEventEntry(_StrictModel):
    """One change record returned on pull or sent on push."""

    id: uuid.UUID | None = None
    entity_type: str
    entity_id: uuid.UUID
    action: str
    revision: int
    payload: dict[str, Any] | None
    created_at: datetime | None = None


class SyncPullResponse(_StrictModel):
    events: list[SyncEventEntry]
    server_timestamp: datetime


class SyncPushRequest(_StrictModel):
    events: list[SyncEventEntry]
    client_timestamp: datetime | None = None


class SyncPushResponse(_StrictModel):
    applied: int
    conflicts: list[dict[str, Any]]
    server_timestamp: datetime
