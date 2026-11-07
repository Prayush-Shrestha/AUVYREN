"""Task service: CRUD, completion, filtering, and progress computation."""

from __future__ import annotations

import uuid
from datetime import date, datetime, time, timedelta

from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate


def utcnow() -> datetime:
    return datetime.now(__import__("datetime").UTC)


async def get_task_by_id(
    db: AsyncSession, *, user_id: uuid.UUID, task_id: uuid.UUID
) -> Task | None:
    result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.user_id == user_id,
            Task.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def create_task(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    payload: TaskCreate,
) -> Task:
    task = Task(
        user_id=user_id,
        project_id=payload.project_id,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        category=payload.category,
        due_at=payload.due_at,
        planned_for=payload.planned_for,
        estimated_minutes=payload.estimated_minutes,
        sort_order=payload.sort_order,
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return task


async def update_task(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    task_id: uuid.UUID,
    payload: TaskUpdate,
) -> Task | None:
    task = await get_task_by_id(db, user_id=user_id, task_id=task_id)
    if task is None:
        return None

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(task, field, value)

    if "status" in data:
        if data["status"] == "done" and task.completed_at is None:
            task.completed_at = utcnow()
        elif data["status"] != "done":
            task.completed_at = None

    await db.flush()
    await db.refresh(task)
    return task


async def delete_task(
    db: AsyncSession, *, user_id: uuid.UUID, task_id: uuid.UUID
) -> Task | None:
    task = await get_task_by_id(db, user_id=user_id, task_id=task_id)
    if task is None:
        return None
    task.deleted_at = utcnow()
    await db.flush()
    return task


async def restore_task(
    db: AsyncSession, *, user_id: uuid.UUID, task_id: uuid.UUID
) -> Task | None:
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.user_id == user_id)
    )
    task = result.scalar_one_or_none()
    if task is None:
        return None
    task.deleted_at = None
    await db.flush()
    return task


async def list_tasks(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    status: str | None = None,
    project_id: uuid.UUID | None = None,
    category: str | None = None,
    planned_for: date | None = None,
    due_before: datetime | None = None,
    include_deleted: bool = False,
    limit: int = 100,
    offset: int = 0,
) -> list[Task]:
    query = select(Task).where(Task.user_id == user_id)

    if not include_deleted:
        query = query.where(Task.deleted_at.is_(None))

    if status is not None:
        query = query.where(text("status = :status")).params(status=status)

    if project_id is not None:
        query = query.where(Task.project_id == project_id)

    if category is not None:
        query = query.where(Task.category == category)

    if planned_for is not None:
        query = query.where(Task.planned_for == planned_for)

    if due_before is not None:
        query = query.where(Task.due_at <= due_before)

    query = query.order_by(Task.sort_order, Task.created_at.desc())
    query = query.limit(limit).offset(offset)

    result = await db.execute(query)
    return list(result.scalars().all())


async def count_tasks(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    status: str | None = None,
    project_id: uuid.UUID | None = None,
    category: str | None = None,
    planned_for: date | None = None,
    due_before: datetime | None = None,
    include_deleted: bool = False,
) -> int:
    query = select(func.count()).select_from(Task).where(Task.user_id == user_id)

    if not include_deleted:
        query = query.where(Task.deleted_at.is_(None))

    if status is not None:
        query = query.where(text("status = :status")).params(status=status)

    if project_id is not None:
        query = query.where(Task.project_id == project_id)

    if category is not None:
        query = query.where(Task.category == category)

    if planned_for is not None:
        query = query.where(Task.planned_for == planned_for)

    if due_before is not None:
        query = query.where(Task.due_at <= due_before)

    result = await db.execute(query)
    return result.scalar_one()


async def get_upcoming_tasks(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    days: int = 7,
    limit: int = 20,
) -> list[Task]:
    now = utcnow()
    end = now + timedelta(days=days)
    query = (
        select(Task)
        .where(
            Task.user_id == user_id,
            Task.deleted_at.is_(None),
            text("status != 'done'"),
        )
        .where(
            or_(
                and_(
                    Task.due_at.is_not(None),
                    Task.due_at >= now,
                    Task.due_at <= end,
                ),
                and_(
                    Task.planned_for.is_not(None),
                    Task.planned_for >= now.date(),
                    Task.planned_for <= end.date(),
                ),
            )
        )
        .order_by(Task.due_at, Task.planned_for, Task.sort_order)
        .limit(limit)
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_today_tasks(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    target_date: date | None = None,
) -> list[Task]:
    day = target_date or utcnow().date()
    start = datetime.combine(day, time.min)
    end = datetime.combine(day, time.max)
    query = (
        select(Task)
        .where(
            Task.user_id == user_id,
            Task.deleted_at.is_(None),
            text("status != 'done'"),
            or_(
                Task.planned_for == day,
                and_(
                    Task.due_at >= start,
                    Task.due_at <= end,
                ),
            )
        )
        .order_by(Task.sort_order, Task.created_at.desc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def search_tasks(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    query_text: str,
    limit: int = 50,
) -> list[Task]:
    like = f"%{query_text}%"
    result = await db.execute(
        select(Task)
        .where(
            Task.user_id == user_id,
            Task.deleted_at.is_(None),
            or_(Task.title.ilike(like), Task.category.ilike(like)),
        )
        .order_by(Task.sort_order, Task.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
