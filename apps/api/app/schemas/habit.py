"""Request and response schemas for habits and habit logs."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.enums import HabitSchedule


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class HabitCreate(_StrictModel):
    name: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=4000)
    schedule: HabitSchedule = HabitSchedule.DAILY
    target_per_week: int | None = Field(default=None, ge=1, le=7)
    start_date: date | None = None


class HabitUpdate(_StrictModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=4000)
    schedule: HabitSchedule | None = None
    target_per_week: int | None = Field(default=None, ge=1, le=7)
    is_archived: bool | None = None


class HabitResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: str | None
    schedule: HabitSchedule
    target_per_week: int | None
    start_date: date
    is_archived: bool
    streak: int
    completions_last_30_days: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HabitListResponse(BaseModel):
    habits: list[HabitResponse]


class HabitLogCreate(_StrictModel):
    log_date: date
    note: str | None = Field(default=None, max_length=1000)


class HabitLogResponse(BaseModel):
    id: uuid.UUID
    habit_id: uuid.UUID
    user_id: uuid.UUID
    log_date: date
    note: str | None
    completed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HabitLogListResponse(BaseModel):
    logs: list[HabitLogResponse]
