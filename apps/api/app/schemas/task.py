"""Request and response schemas for tasks."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.db.models.enums import TaskPriority, TaskStatus


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TaskCreate(_StrictModel):
    title: str = Field(min_length=1, max_length=240)
    description: str | None = Field(default=None, max_length=4000)
    project_id: uuid.UUID | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    category: str | None = Field(default=None, max_length=64)
    due_at: datetime | None = None
    planned_for: date | None = None
    estimated_minutes: int | None = Field(default=None, ge=1)
    sort_order: int = Field(default=0, ge=0)
    status: TaskStatus = TaskStatus.TODO

    @field_validator("category")
    @classmethod
    def _normalize_category(cls, value: str | None) -> str | None:
        if not isinstance(value, str):
            return value
        category = " ".join(value.split())
        return category or None


class TaskUpdate(_StrictModel):
    title: str | None = Field(default=None, min_length=1, max_length=240)
    description: str | None = Field(default=None, max_length=4000)
    project_id: uuid.UUID | None = None
    priority: TaskPriority | None = None
    category: str | None = Field(default=None, max_length=64)
    due_at: datetime | None = None
    planned_for: date | None = None
    estimated_minutes: int | None = Field(default=None, ge=1)
    sort_order: int | None = Field(default=None, ge=0)
    status: TaskStatus | None = None

    @field_validator("category")
    @classmethod
    def _normalize_category(cls, value: str | None) -> str | None:
        if not isinstance(value, str):
            return value
        category = " ".join(value.split())
        return category or None


class TaskResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    project_id: uuid.UUID | None
    title: str
    description: str | None
    status: TaskStatus
    priority: TaskPriority
    category: str | None
    due_at: datetime | None
    planned_for: date | None
    estimated_minutes: int | None
    sort_order: int
    completed_at: datetime | None
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskListResponse(BaseModel):
    tasks: list[TaskResponse]


class TaskStatusUpdate(_StrictModel):
    status: TaskStatus
