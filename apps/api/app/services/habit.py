"""Habit service: CRUD, logging, streak computation."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import AppError
from app.db.models.habit import Habit, HabitLog
from app.schemas.habit import HabitCreate, HabitLogCreate, HabitUpdate


def utcnow() -> datetime:
    return datetime.now(__import__("datetime").UTC)


async def get_habit_by_id(
    db: AsyncSession, *, user_id: uuid.UUID, habit_id: uuid.UUID
) -> Habit | None:
    result = await db.execute(
        select(Habit).where(Habit.id == habit_id, Habit.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def create_habit(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    payload: HabitCreate,
) -> Habit:
    habit = Habit(
        user_id=user_id,
        name=payload.name,
        description=payload.description,
        schedule=payload.schedule,
        target_per_week=payload.target_per_week,
        start_date=payload.start_date or utcnow().date(),
    )
    db.add(habit)
    await db.flush()
    await db.refresh(habit)
    return habit


async def update_habit(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    habit_id: uuid.UUID,
    payload: HabitUpdate,
) -> Habit | None:
    habit = await get_habit_by_id(db, user_id=user_id, habit_id=habit_id)
    if habit is None:
        return None

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(habit, field, value)

    await db.flush()
    await db.refresh(habit)
    return habit


async def archive_habit(
    db: AsyncSession, *, user_id: uuid.UUID, habit_id: uuid.UUID
) -> Habit | None:
    habit = await get_habit_by_id(db, user_id=user_id, habit_id=habit_id)
    if habit is None:
        return None
    habit.is_archived = True
    await db.flush()
    return habit


async def unarchive_habit(
    db: AsyncSession, *, user_id: uuid.UUID, habit_id: uuid.UUID
) -> Habit | None:
    habit = await get_habit_by_id(db, user_id=user_id, habit_id=habit_id)
    if habit is None:
        return None
    habit.is_archived = False
    await db.flush()
    return habit


async def list_habits(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    include_archived: bool = False,
) -> list[Habit]:
    query = select(Habit).where(Habit.user_id == user_id)
    if not include_archived:
        query = query.where(Habit.is_archived == False)  # noqa: E712
    query = query.order_by(Habit.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def compute_streak(
    db: AsyncSession, *, habit: Habit, as_of: date | None = None
) -> int:
    """Compute consecutive-day streak ending at as_of (default today)."""
    today = as_of or utcnow().date()
    logs = await db.execute(
        select(HabitLog.log_date)
        .where(HabitLog.habit_id == habit.id, HabitLog.log_date <= today)
        .order_by(HabitLog.log_date.desc())
    )
    log_dates = [row[0] for row in logs.all()]

    streak = 0
    cursor = today
    for log_date in log_dates:
        if log_date == cursor:
            streak += 1
            cursor -= timedelta(days=1)
        elif log_date < cursor:
            break
    return streak


async def compute_completions_last_30_days(
    db: AsyncSession, *, habit_id: uuid.UUID, as_of: date | None = None
) -> int:
    today = as_of or utcnow().date()
    start = today - timedelta(days=29)
    result = await db.execute(
        select(func.count(HabitLog.id)).where(
            HabitLog.habit_id == habit_id,
            HabitLog.log_date >= start,
            HabitLog.log_date <= today,
        )
    )
    return result.scalar_one()


async def create_habit_log(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    habit_id: uuid.UUID,
    payload: HabitLogCreate,
) -> HabitLog | None:
    # Verify habit ownership
    habit = await get_habit_by_id(db, user_id=user_id, habit_id=habit_id)
    if habit is None:
        return None

    # Check for existing log on same date
    existing = await db.execute(
        select(HabitLog).where(
            HabitLog.habit_id == habit_id, HabitLog.log_date == payload.log_date
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise AppError(
            409,
            "habit_log_already_exists",
            title="Habit already logged for this date",
            detail="A completion already exists for this habit on this date.",
        )

    log = HabitLog(
        habit_id=habit_id,
        user_id=user_id,
        log_date=payload.log_date,
        note=payload.note,
    )
    db.add(log)
    await db.flush()
    await db.refresh(log)
    return log


async def delete_habit_log(
    db: AsyncSession, *, user_id: uuid.UUID, habit_id: uuid.UUID, log_date: date
) -> HabitLog | None:
    habit = await get_habit_by_id(db, user_id=user_id, habit_id=habit_id)
    if habit is None:
        return None

    result = await db.execute(
        select(HabitLog).where(
            HabitLog.habit_id == habit_id, HabitLog.log_date == log_date
        )
    )
    log = result.scalar_one_or_none()
    if log is None:
        return None

    await db.delete(log)
    await db.flush()
    return log


async def list_habit_logs(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    habit_id: uuid.UUID,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[HabitLog]:
    habit = await get_habit_by_id(db, user_id=user_id, habit_id=habit_id)
    if habit is None:
        return []

    query = select(HabitLog).where(HabitLog.habit_id == habit_id)
    if start_date is not None:
        query = query.where(HabitLog.log_date >= start_date)
    if end_date is not None:
        query = query.where(HabitLog.log_date <= end_date)
    query = query.order_by(HabitLog.log_date.desc())

    result = await db.execute(query)
    return list(result.scalars().all())
