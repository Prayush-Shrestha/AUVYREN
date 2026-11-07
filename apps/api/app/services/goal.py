"""Goal service: CRUD, progress computation, milestone management."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import AppError
from app.db.models.goal import Goal
from app.db.models.milestone import Milestone
from app.schemas.goal import GoalCreate, GoalUpdate, MilestoneCreate, MilestoneUpdate


def utcnow() -> datetime:
    return datetime.now(__import__("datetime").UTC)


async def get_goal_by_id(
    db: AsyncSession, *, user_id: uuid.UUID, goal_id: uuid.UUID
) -> Goal | None:
    result = await db.execute(
        select(Goal)
        .where(Goal.id == goal_id, Goal.user_id == user_id)
        .options(__import__("sqlalchemy.orm", fromlist=["selectinload"]).selectinload(Goal.milestones))
    )
    return result.scalar_one_or_none()


async def create_goal(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    payload: GoalCreate,
) -> Goal:
    goal = Goal(
        user_id=user_id,
        title=payload.title,
        description=payload.description,
        outcome=payload.outcome,
        target_date=payload.target_date,
        manual_progress=payload.manual_progress,
    )
    db.add(goal)
    await db.flush()
    await db.refresh(goal, attribute_names=["milestones"])
    return goal


async def update_goal(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    goal_id: uuid.UUID,
    payload: GoalUpdate,
) -> Goal | None:
    goal = await get_goal_by_id(db, user_id=user_id, goal_id=goal_id)
    if goal is None:
        return None

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(goal, field, value)

    if data.get("status") is not None:
        if data["status"] == "completed" and goal.completed_at is None:
            goal.completed_at = utcnow()
        elif data["status"] != "completed":
            goal.completed_at = None

    await db.flush()
    await db.refresh(goal, attribute_names=["milestones"])
    return goal


async def delete_goal(
    db: AsyncSession, *, user_id: uuid.UUID, goal_id: uuid.UUID
) -> Goal | None:
    goal = await get_goal_by_id(db, user_id=user_id, goal_id=goal_id)
    if goal is None:
        return None
    goal.deleted_at = utcnow()
    await db.flush()
    return goal


async def restore_goal(
    db: AsyncSession, *, user_id: uuid.UUID, goal_id: uuid.UUID
) -> Goal | None:
    goal = await get_goal_by_id(db, user_id=user_id, goal_id=goal_id)
    if goal is None:
        return None
    goal.deleted_at = None
    await db.flush()
    return goal


async def list_goals(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    status: str | None = None,
    include_deleted: bool = False,
    limit: int = 100,
    offset: int = 0,
) -> list[Goal]:
    query = select(Goal).where(Goal.user_id == user_id)

    if not include_deleted:
        query = query.where(Goal.deleted_at.is_(None))

    if status is not None:
        query = query.where(Goal.status == status)

    query = query.order_by(Goal.created_at.desc()).limit(limit).offset(offset)

    result = await db.execute(query.options(__import__("sqlalchemy.orm", fromlist=["selectinload"]).selectinload(Goal.milestones)))
    return list(result.scalars().all())


async def compute_goal_progress(goal: Goal) -> tuple[int, int, int]:
    """Return (progress, milestone_count, completed_milestone_count)."""
    milestones = list(goal.milestones or [])
    milestone_count = len(milestones)
    completed_count = sum(1 for m in milestones if m.status == "completed")

    if goal.manual_progress is not None:
        progress = goal.manual_progress
    elif milestone_count > 0:
        progress = int(round((completed_count / milestone_count) * 100))
    else:
        progress = 100 if goal.status == "completed" else 0

    return progress, milestone_count, completed_count


def serialize_goal_response(goal: Goal) -> dict:
    progress, milestone_count, completed_count = compute_goal_progress(goal)
    return {
        "id": goal.id,
        "user_id": goal.user_id,
        "title": goal.title,
        "description": goal.description,
        "outcome": goal.outcome,
        "status": goal.status,
        "target_date": goal.target_date,
        "completed_at": goal.completed_at,
        "manual_progress": goal.manual_progress,
        "deleted_at": goal.deleted_at,
        "created_at": goal.created_at,
        "updated_at": goal.updated_at,
        "progress": progress,
        "milestone_count": milestone_count,
        "completed_milestone_count": completed_count,
    }


# Milestones


async def get_milestone_by_id(
    db: AsyncSession, *, goal_id: uuid.UUID, milestone_id: uuid.UUID
) -> Milestone | None:
    result = await db.execute(
        select(Milestone).where(
            Milestone.id == milestone_id, Milestone.goal_id == goal_id
        )
    )
    return result.scalar_one_or_none()


async def create_milestone(
    db: AsyncSession,
    *,
    goal_id: uuid.UUID,
    payload: MilestoneCreate,
) -> Milestone:
    milestone = Milestone(
        goal_id=goal_id,
        title=payload.title,
        description=payload.description,
        target_date=payload.target_date,
        sort_order=payload.sort_order,
    )
    db.add(milestone)
    await db.flush()
    await db.refresh(milestone)
    return milestone


async def update_milestone(
    db: AsyncSession,
    *,
    goal_id: uuid.UUID,
    milestone_id: uuid.UUID,
    payload: MilestoneUpdate,
) -> Milestone | None:
    milestone = await get_milestone_by_id(db, goal_id=goal_id, milestone_id=milestone_id)
    if milestone is None:
        return None

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(milestone, field, value)

    if data.get("status") is not None:
        if data["status"] == "completed" and milestone.completed_at is None:
            milestone.completed_at = utcnow()
        elif data["status"] != "completed":
            milestone.completed_at = None

    await db.flush()
    await db.refresh(milestone)
    return milestone


async def delete_milestone(
    db: AsyncSession, *, goal_id: uuid.UUID, milestone_id: uuid.UUID
) -> Milestone | None:
    milestone = await get_milestone_by_id(db, goal_id=goal_id, milestone_id=milestone_id)
    if milestone is None:
        return None
    await db.delete(milestone)
    await db.flush()
    return milestone


async def list_milestones(
    db: AsyncSession, *, goal_id: uuid.UUID
) -> list[Milestone]:
    result = await db.execute(
        select(Milestone)
        .where(Milestone.goal_id == goal_id)
        .order_by(Milestone.sort_order, Milestone.created_at)
    )
    return list(result.scalars().all())
