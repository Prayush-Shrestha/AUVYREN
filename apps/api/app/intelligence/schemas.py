"""Pydantic schemas for the intelligence engine API."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TaskScoreResponse(BaseModel):
    task_id: uuid.UUID
    title: str
    score: int = Field(ge=0, le=100)
    reasons: list[str]


class TaskPrioritizeResponse(BaseModel):
    prioritized: list[TaskScoreResponse]


class DailyPlanResponse(BaseModel):
    date: date
    available_minutes: int
    estimated_remaining_minutes: int
    overload: bool
    priorities: list[TaskScoreResponse]
    focus_block_minutes: int
    slack_minutes: int


class DeadlineItemResponse(BaseModel):
    kind: Literal["task", "goal", "milestone"]
    id: uuid.UUID
    title: str
    due: date
    classification: str


class DeadlineAwarenessResponse(BaseModel):
    items: list[DeadlineItemResponse]


class GoalProgressResponse(BaseModel):
    goal_id: uuid.UUID
    title: str
    progress: int = Field(ge=0, le=100)
    milestone_count: int
    completed_milestone_count: int
    is_neglected: bool


class HabitConsistencyResponse(BaseModel):
    habit_id: uuid.UUID
    name: str
    schedule: str
    streak: int
    completions_7d: int
    completions_30d: int
    completion_rate_7d: float
    completion_rate_30d: float
    missed_dates_7d: list[date]
    is_inconsistent: bool


class PatternResponse(BaseModel):
    kind: str
    description: str
    evidence: str
    confidence: Literal["low", "medium", "high"]


class WeeklyReviewDraftResponse(BaseModel):
    week_start: date
    completed_count: int
    missed_count: int
    habit_consistency_summary: str
    goal_movement_summary: str
    overload_warning: str | None
    priorities_next_week: list[str]


class BriefingResponse(BaseModel):
    date: date
    daily_plan: DailyPlanResponse | None
    deadlines: list[DeadlineItemResponse]
    goal_progress: list[GoalProgressResponse]
    habit_consistency: list[HabitConsistencyResponse]
    patterns: list[PatternResponse]


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    provider: str = "deterministic"
    model: str | None = None


class AskResponse(BaseModel):
    answer: str
    provider: str
    model: str | None
    usage: dict | None
    generated_at: str


class ProviderInfoResponse(BaseModel):
    name: str
    healthy: bool
    detail: str
    models: list[str]


class ProviderConfigureRequest(BaseModel):
    provider: str = "ollama"
    base_url: str = Field(min_length=1, max_length=500)
    model: str = Field(min_length=1, max_length=100)


class ProviderConfigureResponse(BaseModel):
    provider: str
    base_url: str
    model: str
    healthy: bool
    detail: str
    secret_hash: str | None  # hash of stored secret for change detection


class ProviderSecretResponse(BaseModel):
    secret_hash: str | None


class InsightResponse(BaseModel):
    id: uuid.UUID
    kind: str
    title: str
    content: str
    provider: str
    model: str | None
    generated_at: datetime
    dismissed: bool


class UsageLogResponse(BaseModel):
    id: uuid.UUID
    request_type: str
    provider: str
    model: str | None
    tokens_in: int | None
    tokens_out: int | None
    estimated_cost: float | None
    success: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
