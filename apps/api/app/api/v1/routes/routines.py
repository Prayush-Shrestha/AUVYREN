"""Routine and routine-step endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_auth
from app.api.errors import AppError
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
    get_routine_step_by_id,
    list_routines,
    update_routine,
    update_routine_step,
)

router = APIRouter(prefix="/routines", tags=["Routines"], dependencies=[Depends(require_csrf)])


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
    return RoutineResponse(
        id=routine.id,
        user_id=routine.user_id,
        name=routine.name,
        description=routine.description,
        time_of_day=routine.time_of_day,
        is_active=routine.is_active,
        step_count=len(routine.steps or []),
        created_at=routine.created_at,
        updated_at=routine.updated_at,
        steps=[
            RoutineStepResponse.model_validate(s) for s in (routine.steps or [])
        ],
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
        routines=[
            RoutineResponse(
                id=r.id,
                user_id=r.user_id,
                name=r.name,
                description=r.description,
                time_of_day=r.time_of_day,
                is_active=r.is_active,
                step_count=len(r.steps or []),
                created_at=r.created_at,
                updated_at=r.updated_at,
                steps=[RoutineStepResponse.model_validate(s) for s in (r.steps or [])],
            )
            for r in routines
        ]
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
    return RoutineResponse(
        id=routine.id,
        user_id=routine.user_id,
        name=routine.name,
        description=routine.description,
        time_of_day=routine.time_of_day,
        is_active=routine.is_active,
        step_count=len(routine.steps or []),
        created_at=routine.created_at,
        updated_at=routine.updated_at,
        steps=[RoutineStepResponse.model_validate(s) for s in (routine.steps or [])],
    )


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
    return RoutineResponse(
        id=routine.id,
        user_id=routine.user_id,
        name=routine.name,
        description=routine.description,
        time_of_day=routine.time_of_day,
        is_active=routine.is_active,
        step_count=len(routine.steps or []),
        created_at=routine.created_at,
        updated_at=routine.updated_at,
        steps=[RoutineStepResponse.model_validate(s) for s in (routine.steps or [])],
    )


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
    # Verify routine ownership
    result = await db.execute(
        __import__("sqlalchemy", fromlist=["select"]).select(
            __import__("app.db.models.routine", fromlist=["Routine"]).Routine
        ).where(
            __import__("app.db.models.routine", fromlist=["Routine"]).Routine.id == __import__("app.db.models.routine", fromlist=["RoutineStep"]).RoutineStep.routine_id,
            __import__("app.db.models.routine", fromlist=["RoutineStep"]).RoutineStep.id == step_id,
            __import__("app.db.models.routine", fromlist=["Routine"]).Routine.user_id == auth.user.id,
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
    # Verify routine ownership
    result = await db.execute(
        __import__("sqlalchemy", fromlist=["select"]).select(
            __import__("app.db.models.routine", fromlist=["Routine"]).Routine
        ).where(
            __import__("app.db.models.routine", fromlist=["Routine"]).Routine.id == __import__("app.db.models.routine", fromlist=["RoutineStep"]).RoutineStep.routine_id,
            __import__("app.db.models.routine", fromlist=["RoutineStep"]).RoutineStep.id == step_id,
            __import__("app.db.models.routine", fromlist=["Routine"]).Routine.user_id == auth.user.id,
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
    response.status_code = status.HTTP_204_NO_CONTENT
