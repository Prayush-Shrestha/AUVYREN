"""Request and response schemas for goals and milestones."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.db.models.enums import GoalStatus, MilestoneStatus


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class GoalCreate(_StrictModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    outcome: str | None = Field(default=None, max_length=4000)
    target_date: date | None = None
    manual_progress: int | None = Field(default=None, ge=0, le=100)


class GoalUpdate(_StrictModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    outcome: str | None = Field(default=None, max_length=4000)
    target_date: date | None = None
    manual_progress: int | None = Field(default=None, ge=0, le=100)
    status: GoalStatus | None = None


class GoalResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    description: str | None
    outcome: str | None
    status: GoalStatus
    target_date: date | None
    completed_at: datetime | None
    manual_progress: int | None
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime
    progress: int
    milestone_count: int
    completed_milestone_count: int

    model_config = ConfigDict(from_attributes=True)


class GoalListResponse(BaseModel):
    goals: list[GoalResponse]


class MilestoneCreate(_StrictModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    target_date: date | None = None
    sort_order: int = Field(default=0, ge=0)


class MilestoneUpdate(_StrictModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    target_date: date | None = None
    status: MilestoneStatus | None = None
    sort_order: int | None = Field(default=None, ge=0)


class MilestoneResponse(BaseModel):
    id: uuid.UUID
    goal_id: uuid.UUID
    title: str
    description: str | None
    status: MilestoneStatus
    target_date: date | None
    completed_at: datetime | None
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MilestoneListResponse(BaseModel):
    milestones: list[MilestoneResponse]
