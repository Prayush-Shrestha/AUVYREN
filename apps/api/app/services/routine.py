"""Routine service: CRUD and step management."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.routine import Routine, RoutineStep
from app.schemas.routine import (
    RoutineCreate,
    RoutineStepCreate,
    RoutineStepUpdate,
    RoutineUpdate,
)


def utcnow() -> datetime:
    return datetime.now(__import__("datetime").UTC)


async def get_routine_by_id(
    db: AsyncSession, *, user_id: uuid.UUID, routine_id: uuid.UUID
) -> Routine | None:
    result = await db.execute(
        select(Routine)
        .where(Routine.id == routine_id, Routine.user_id == user_id)
        .options(__import__("sqlalchemy.orm", fromlist=["selectinload"]).selectinload(Routine.steps))
    )
    return result.scalar_one_or_none()


async def create_routine(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    payload: RoutineCreate,
) -> Routine:
    routine = Routine(
        user_id=user_id,
        name=payload.name,
        description=payload.description,
        time_of_day=payload.time_of_day,
        is_active=payload.is_active,
    )
    db.add(routine)
    await db.flush()

    for step_data in payload.steps:
        step = RoutineStep(
            routine_id=routine.id,
            title=step_data.title,
            description=step_data.description,
            duration_minutes=step_data.duration_minutes,
            sort_order=step_data.sort_order,
        )
        db.add(step)

    await db.flush()
    await db.refresh(routine, attribute_names=["steps"])
    return routine


async def update_routine(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    routine_id: uuid.UUID,
    payload: RoutineUpdate,
) -> Routine | None:
    routine = await get_routine_by_id(db, user_id=user_id, routine_id=routine_id)
    if routine is None:
        return None

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(routine, field, value)

    await db.flush()
    await db.refresh(routine, attribute_names=["steps"])
    return routine


async def delete_routine(
    db: AsyncSession, *, user_id: uuid.UUID, routine_id: uuid.UUID
) -> Routine | None:
    routine = await get_routine_by_id(db, user_id=user_id, routine_id=routine_id)
    if routine is None:
        return None
    await db.delete(routine)
    await db.flush()
    return routine


async def list_routines(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    include_inactive: bool = False,
) -> list[Routine]:
    query = select(Routine).where(Routine.user_id == user_id)
    if not include_inactive:
        query = query.where(Routine.is_active == True)  # noqa: E712
    query = query.options(
        __import__("sqlalchemy.orm", fromlist=["selectinload"]).selectinload(Routine.steps)
    ).order_by(Routine.created_at.desc())

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_routine_step_by_id(
    db: AsyncSession, *, routine_id: uuid.UUID, step_id: uuid.UUID
) -> RoutineStep | None:
    result = await db.execute(
        select(RoutineStep).where(
            RoutineStep.id == step_id, RoutineStep.routine_id == routine_id
        )
    )
    return result.scalar_one_or_none()


async def create_routine_step(
    db: AsyncSession,
    *,
    routine_id: uuid.UUID,
    payload: RoutineStepCreate,
) -> RoutineStep:
    step = RoutineStep(
        routine_id=routine_id,
        title=payload.title,
        description=payload.description,
        duration_minutes=payload.duration_minutes,
        sort_order=payload.sort_order,
    )
    db.add(step)
    await db.flush()
    await db.refresh(step)
    return step


async def update_routine_step(
    db: AsyncSession,
    *,
    routine_id: uuid.UUID,
    step_id: uuid.UUID,
    payload: RoutineStepUpdate,
) -> RoutineStep | None:
    step = await get_routine_step_by_id(db, routine_id=routine_id, step_id=step_id)
    if step is None:
        return None

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(step, field, value)

    await db.flush()
    await db.refresh(step)
    return step


async def delete_routine_step(
    db: AsyncSession, *, routine_id: uuid.UUID, step_id: uuid.UUID
) -> RoutineStep | None:
    step = await get_routine_step_by_id(db, routine_id=routine_id, step_id=step_id)
    if step is None:
        return None
    await db.delete(step)
    await db.flush()
    return step
