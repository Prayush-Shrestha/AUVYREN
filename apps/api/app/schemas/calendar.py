"""Request and response schemas for calendar events."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CalendarEventCreate(_StrictModel):
    title: str = Field(min_length=1, max_length=240)
    description: str | None = Field(default=None, max_length=4000)
    project_id: uuid.UUID | None = None
    starts_at: datetime
    ends_at: datetime
    all_day: bool = False
    location: str | None = Field(default=None, max_length=240)

    @model_validator(mode="after")
    def _validate_time_range(self) -> CalendarEventCreate:
        if self.ends_at <= self.starts_at:
            raise ValueError("Ends at must be after starts at.")
        return self


class CalendarEventUpdate(_StrictModel):
    title: str | None = Field(default=None, min_length=1, max_length=240)
    description: str | None = Field(default=None, max_length=4000)
    project_id: uuid.UUID | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    all_day: bool | None = None
    location: str | None = Field(default=None, max_length=240)

    @model_validator(mode="after")
    def _validate_time_range(self) -> CalendarEventUpdate:
        if self.starts_at is not None and self.ends_at is not None:
            if self.ends_at <= self.starts_at:
                raise ValueError("Ends at must be after starts at.")
        return self


class CalendarEventResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    project_id: uuid.UUID | None
    title: str
    description: str | None
    starts_at: datetime
    ends_at: datetime
    all_day: bool
    location: str | None
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CalendarEventListResponse(BaseModel):
    events: list[CalendarEventResponse]
