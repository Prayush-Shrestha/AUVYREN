"""Request and response schemas for routines and routine steps."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RoutineStepCreate(_StrictModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    duration_minutes: int | None = Field(default=None, ge=1, le=1440)
    sort_order: int = Field(default=0, ge=0)


class RoutineStepUpdate(_StrictModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    duration_minutes: int | None = Field(default=None, ge=1, le=1440)
    sort_order: int | None = Field(default=None, ge=0)


class RoutineStepResponse(BaseModel):
    id: uuid.UUID
    routine_id: uuid.UUID
    title: str
    description: str | None
    duration_minutes: int | None
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RoutineCreate(_StrictModel):
    name: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=4000)
    time_of_day: str | None = Field(default=None, max_length=32)
    is_active: bool = True
    steps: list[RoutineStepCreate] = []


class RoutineUpdate(_StrictModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=4000)
    time_of_day: str | None = Field(default=None, max_length=32)
    is_active: bool | None = None


class RoutineResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: str | None
    time_of_day: str | None
    is_active: bool
    step_count: int
    created_at: datetime
    updated_at: datetime
    steps: list[RoutineStepResponse] = []

    model_config = ConfigDict(from_attributes=True)


class RoutineListResponse(BaseModel):
    routines: list[RoutineResponse]
