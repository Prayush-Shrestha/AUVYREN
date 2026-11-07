"""Request and response schemas for projects."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.db.models.enums import ProjectStatus


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProjectCreate(_StrictModel):
    name: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=4000)
    status: ProjectStatus = ProjectStatus.ACTIVE
    start_date: date | None = None
    due_date: date | None = None

    @model_validator(mode="after")
    def _validate_dates(self) -> "ProjectCreate":
        if self.start_date is not None and self.due_date is not None:
            if self.due_date < self.start_date:
                raise ValueError("Due date must be on or after start date.")
        return self


class ProjectUpdate(_StrictModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=4000)
    status: ProjectStatus | None = None
    start_date: date | None = None
    due_date: date | None = None

    @model_validator(mode="after")
    def _validate_dates(self) -> "ProjectUpdate":
        if self.start_date is not None and self.due_date is not None:
            if self.due_date < self.start_date:
                raise ValueError("Due date must be on or after start date.")
        return self


class ProjectResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: str | None
    status: ProjectStatus
    start_date: date | None
    due_date: date | None
    deleted_at: datetime | None
    task_count: int
    completed_task_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProjectListResponse(BaseModel):
    projects: list[ProjectResponse]
