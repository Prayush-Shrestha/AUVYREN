"""Habit and habit-log endpoints."""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_auth
from app.api.errors import AppError
from app.db.session import get_db_session
from app.schemas.habit import (
    HabitCreate,
    HabitListResponse,
    HabitLogCreate,
    HabitLogListResponse,
    HabitLogResponse,
    HabitResponse,
    HabitUpdate,
)
from app.services.auth import CurrentAuth
from app.services.habit import (
    archive_habit,
    compute_completions_last_30_days,
    compute_streak,
    create_habit,
    create_habit_log,
    delete_habit_log,
    list_habit_logs,
    list_habits,
    unarchive_habit,
    update_habit,
)

router = APIRouter(prefix="/habits", tags=["Habits"], dependencies=[Depends(require_csrf)])


@router.post(
    "",
    response_model=HabitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a habit",
)
async def create_habit_endpoint(
    payload: HabitCreate,
    request: Request,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> HabitResponse:
    habit = await create_habit(db, user_id=auth.user.id, payload=payload)
    streak = await compute_streak(db, habit=habit)
    completions = await compute_completions_last_30_days(db, habit_id=habit.id)
    return HabitResponse(
        **habit.__dict__,
        streak=streak,
        completions_last_30_days=completions,
    )


@router.get(
    "",
    response_model=HabitListResponse,
    summary="List habits",
)
async def list_habits_endpoint(
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
    include_archived: bool = Query(False),
) -> HabitListResponse:
    habits = await list_habits(db, user_id=auth.user.id, include_archived=include_archived)
    items = []
    for habit in habits:
        streak = await compute_streak(db, habit=habit)
        completions = await compute_completions_last_30_days(db, habit_id=habit.id)
        items.append(
            HabitResponse(
                **habit.__dict__,
                streak=streak,
                completions_last_30_days=completions,
            )
        )
    return HabitListResponse(habits=items)


@router.get(
    "/{habit_id}",
    response_model=HabitResponse,
    summary="Get a single habit",
)
async def get_habit_endpoint(
    habit_id: uuid.UUID,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> HabitResponse:
    result = await db.execute(
        __import__("sqlalchemy", fromlist=["select"]).select(
            __import__("app.db.models.habit", fromlist=["Habit"]).Habit
        ).where(
            __import__("app.db.models.habit", fromlist=["Habit"]).Habit.id == habit_id,
            __import__("app.db.models.habit", fromlist=["Habit"]).Habit.user_id == auth.user.id,
        )
    )
    habit = result.scalar_one_or_none()
    if habit is None:
        raise AppError(
            404,
            "habit_not_found",
            title="Habit not found",
            detail="That habit does not exist.",
        )
    streak = await compute_streak(db, habit=habit)
    completions = await compute_completions_last_30_days(db, habit_id=habit.id)
    return HabitResponse(
        **habit.__dict__,
        streak=streak,
        completions_last_30_days=completions,
    )


@router.patch(
    "/{habit_id}",
    response_model=HabitResponse,
    summary="Update a habit",
)
async def update_habit_endpoint(
    habit_id: uuid.UUID,
    payload: HabitUpdate,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> HabitResponse:
    habit = await update_habit(db, user_id=auth.user.id, habit_id=habit_id, payload=payload)
    if habit is None:
        raise AppError(
            404,
            "habit_not_found",
            title="Habit not found",
            detail="That habit does not exist.",
        )
    streak = await compute_streak(db, habit=habit)
    completions = await compute_completions_last_30_days(db, habit_id=habit.id)
    return HabitResponse(
        **habit.__dict__,
        streak=streak,
        completions_last_30_days=completions,
    )


@router.post(
    "/{habit_id}/archive",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Archive a habit",
)
async def archive_habit_endpoint(
    habit_id: uuid.UUID,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    habit = await archive_habit(db, user_id=auth.user.id, habit_id=habit_id)
    if habit is None:
        raise AppError(
            404,
            "habit_not_found",
            title="Habit not found",
            detail="That habit does not exist.",
        )
    response.status_code = status.HTTP_204_NO_CONTENT


@router.post(
    "/{habit_id}/unarchive",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unarchive a habit",
)
async def unarchive_habit_endpoint(
    habit_id: uuid.UUID,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    habit = await unarchive_habit(db, user_id=auth.user.id, habit_id=habit_id)
    if habit is None:
        raise AppError(
            404,
            "habit_not_found",
            title="Habit not found",
            detail="That habit does not exist.",
        )
    response.status_code = status.HTTP_204_NO_CONTENT


# Habit logs


@router.post(
    "/{habit_id}/logs",
    response_model=HabitLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log a habit completion",
)
async def create_habit_log_endpoint(
    habit_id: uuid.UUID,
    payload: HabitLogCreate,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> HabitLogResponse:
    log = await create_habit_log(
        db, user_id=auth.user.id, habit_id=habit_id, payload=payload
    )
    if log is None:
        raise AppError(
            404,
            "habit_not_found",
            title="Habit not found",
            detail="That habit does not exist.",
        )
    return HabitLogResponse.model_validate(log)


@router.get(
    "/{habit_id}/logs",
    response_model=HabitLogListResponse,
    summary="List habit completion logs",
)
async def list_habit_logs_endpoint(
    habit_id: uuid.UUID,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
    start_date: date | None = Query(None),
    end_date: date | None = Query(None),
) -> HabitLogListResponse:
    logs = await list_habit_logs(
        db,
        user_id=auth.user.id,
        habit_id=habit_id,
        start_date=start_date,
        end_date=end_date,
    )
    return HabitLogListResponse(logs=[HabitLogResponse.model_validate(l) for l in logs])


@router.delete(
    "/{habit_id}/logs/{log_date}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a habit completion log",
)
async def delete_habit_log_endpoint(
    habit_id: uuid.UUID,
    log_date: date,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    log = await delete_habit_log(
        db, user_id=auth.user.id, habit_id=habit_id, log_date=log_date
    )
    if log is None:
        raise AppError(
            404,
            "habit_log_not_found",
            title="Habit log not found",
            detail="No completion logged for this date.",
        )
    response.status_code = status.HTTP_204_NO_CONTENT
