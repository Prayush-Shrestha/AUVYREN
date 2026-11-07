"""Routine and routine-step endpoints."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_auth, require_csrf
from app.api.errors import AppError
from app.db.models.routine import Routine, RoutineStep
from app.db.session import get_db_session
from app.schemas.routine import (
    RoutineCreate,
    RoutineListResponse,
    RoutineResponse,
    RoutineStepCreate,
    RoutineStepResponse,
    RoutineStepUpdate,
    RoutineUpdate,
)
from app.services.auth import CurrentAuth
from app.services.routine import (
    create_routine,
    create_routine_step,
    delete_routine,
    delete_routine_step,
    get_routine_by_id,
    list_routines,
    update_routine,
    update_routine_step,
)

router = APIRouter(prefix="/routines", tags=["Routines"], dependencies=[Depends(require_csrf)])


def _routine_response(routine: Routine) -> RoutineResponse:
    insp = inspect(routine)
    return RoutineResponse(
        id=insp.attrs["id"].value,
        user_id=insp.attrs["user_id"].value,
        name=insp.attrs["name"].value,
        description=insp.attrs["description"].value,
        time_of_day=insp.attrs["time_of_day"].value,
        is_active=insp.attrs["is_active"].value,
        step_count=len(routine.steps or []),
        created_at=insp.attrs["created_at"].value,
        updated_at=insp.attrs["updated_at"].value,
        steps=[RoutineStepResponse.model_validate(s) for s in (routine.steps or [])],
    )


@router.post(
    "",
    response_model=RoutineResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a routine",
)
async def create_routine_endpoint(
    payload: RoutineCreate,
    request: Request,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> RoutineResponse:
    routine = await create_routine(db, user_id=auth.user.id, payload=payload)
    await db.commit()
    # Build step responses from payload (ORM relationship access after flush
    # requires async IO which is not available in sync response building)
    step_responses = [
        RoutineStepResponse(
            id=uuid.uuid4(),
            routine_id=routine.id,
            title=step.title,
            description=step.description,
            duration_minutes=step.duration_minutes,
            sort_order=step.sort_order,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        for step in payload.steps
    ]
    return RoutineResponse(
        id=routine.id,
        user_id=routine.user_id,
        name=routine.name,
        description=routine.description,
        time_of_day=routine.time_of_day,
        is_active=routine.is_active,
        step_count=len(payload.steps),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        steps=step_responses,
    )

@router.get(
    "",
    response_model=RoutineListResponse,
    summary="List routines",
)
async def list_routines_endpoint(
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
    include_inactive: bool = Query(False),
) -> RoutineListResponse:
    routines = await list_routines(
        db, user_id=auth.user.id, include_inactive=include_inactive
    )
    return RoutineListResponse(
        routines=[_routine_response(r) for r in routines]
    )


@router.get(
    "/{routine_id}",
    response_model=RoutineResponse,
    summary="Get a single routine",
)
async def get_routine_endpoint(
    routine_id: uuid.UUID,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> RoutineResponse:
    routine = await get_routine_by_id(db, user_id=auth.user.id, routine_id=routine_id)
    if routine is None:
        raise AppError(
            404,
            "routine_not_found",
            title="Routine not found",
            detail="That routine does not exist.",
        )
    return _routine_response(routine)


@router.patch(
    "/{routine_id}",
    response_model=RoutineResponse,
    summary="Update a routine",
)
async def update_routine_endpoint(
    routine_id: uuid.UUID,
    payload: RoutineUpdate,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> RoutineResponse:
    routine = await update_routine(
        db, user_id=auth.user.id, routine_id=routine_id, payload=payload
    )
    if routine is None:
        raise AppError(
            404,
            "routine_not_found",
            title="Routine not found",
            detail="That routine does not exist.",
        )
    response_data = _routine_response(routine)
    await db.commit()
    return response_data


@router.delete(
    "/{routine_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a routine",
)
async def delete_routine_endpoint(
    routine_id: uuid.UUID,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    deleted = await delete_routine(db, user_id=auth.user.id, routine_id=routine_id)
    if deleted is None:
        raise AppError(
            404,
            "routine_not_found",
            title="Routine not found",
            detail="That routine does not exist.",
        )
    await db.commit()
    response.status_code = status.HTTP_204_NO_CONTENT


# Routine steps


@router.post(
    "/{routine_id}/steps",
    response_model=RoutineStepResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a step to a routine",
)
async def create_routine_step_endpoint(
    routine_id: uuid.UUID,
    payload: RoutineStepCreate,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> RoutineStepResponse:
    routine = await get_routine_by_id(db, user_id=auth.user.id, routine_id=routine_id)
    if routine is None:
        raise AppError(
            404,
            "routine_not_found",
            title="Routine not found",
            detail="That routine does not exist.",
        )
    step = await create_routine_step(db, routine_id=routine_id, payload=payload)
    await db.commit()
    await db.refresh(step)
    return RoutineStepResponse.model_validate(step)


@router.patch(
    "/steps/{step_id}",
    response_model=RoutineStepResponse,
    summary="Update a routine step",
)
async def update_routine_step_endpoint(
    step_id: uuid.UUID,
    payload: RoutineStepUpdate,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> RoutineStepResponse:
    result = await db.execute(
        select(Routine)
        .join(RoutineStep, RoutineStep.routine_id == Routine.id)
        .where(
            RoutineStep.id == step_id,
            Routine.user_id == auth.user.id,
        )
    )
    routine = result.scalar_one_or_none()
    if routine is None:
        raise AppError(
            404,
            "routine_not_found",
            title="Routine not found",
            detail="That routine does not exist.",
        )

    step = await update_routine_step(
        db, routine_id=routine.id, step_id=step_id, payload=payload
    )
    if step is None:
        raise AppError(
            404,
            "step_not_found",
            title="Step not found",
            detail="That step does not exist.",
        )
    await db.commit()
    await db.refresh(step)
    return RoutineStepResponse.model_validate(step)


@router.delete(
    "/steps/{step_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a routine step",
)
async def delete_routine_step_endpoint(
    step_id: uuid.UUID,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    result = await db.execute(
        select(Routine)
        .join(RoutineStep, RoutineStep.routine_id == Routine.id)
        .where(
            RoutineStep.id == step_id,
            Routine.user_id == auth.user.id,
        )
    )
    routine = result.scalar_one_or_none()
    if routine is None:
        raise AppError(
            404,
            "routine_not_found",
            title="Routine not found",
            detail="That routine does not exist.",
        )

    deleted = await delete_routine_step(db, routine_id=routine.id, step_id=step_id)
    if deleted is None:
        raise AppError(
            404,
            "step_not_found",
            title="Step not found",
            detail="That step does not exist.",
        )
    await db.commit()
    response.status_code = status.HTTP_204_NO_CONTENT
