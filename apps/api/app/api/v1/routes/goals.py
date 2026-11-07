"""Goal and milestone endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_auth, require_csrf
from app.api.errors import AppError
from app.db.models import Goal, Milestone
from app.db.session import get_db_session
from app.schemas.goal import (
    GoalCreate,
    GoalListResponse,
    GoalResponse,
    GoalUpdate,
    MilestoneCreate,
    MilestoneListResponse,
    MilestoneResponse,
    MilestoneUpdate,
)
from app.services.auth import CurrentAuth
from app.services.goal import (
    compute_goal_progress,
    create_goal,
    create_milestone,
    delete_goal,
    delete_milestone,
    get_goal_by_id,
    list_goals,
    list_milestones,
    restore_goal,
    serialize_goal_response,
    update_goal,
    update_milestone,
)

router = APIRouter(prefix="/goals", tags=["Goals"], dependencies=[Depends(require_csrf)])


@router.post(
    "",
    response_model=GoalResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a goal",
)
async def create_goal_endpoint(
    payload: GoalCreate,
    request: Request,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> GoalResponse:
    goal = await create_goal(db, user_id=auth.user.id, payload=payload)
    await db.commit()
    await db.refresh(goal, attribute_names=["milestones"])
    progress, milestone_count, completed_count = compute_goal_progress(goal)
    return GoalResponse(
        **serialize_goal_response(goal),
        progress=progress,
        milestone_count=milestone_count,
        completed_milestone_count=completed_count,
    )


@router.get(
    "",
    response_model=GoalListResponse,
    summary="List goals",
)
async def list_goals_endpoint(
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
    status: str | None = Query(None),
    include_deleted: bool = Query(False),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> GoalListResponse:
    goals = await list_goals(
        db,
        user_id=auth.user.id,
        status=status,
        include_deleted=include_deleted,
        limit=limit,
        offset=offset,
    )
    items = []
    for goal in goals:
        progress, milestone_count, completed_count = compute_goal_progress(goal)
        items.append(
            GoalResponse(
                **serialize_goal_response(goal),
                progress=progress,
                milestone_count=milestone_count,
                completed_milestone_count=completed_count,
            )
        )
    return GoalListResponse(goals=items)


@router.get(
    "/{goal_id}",
    response_model=GoalResponse,
    summary="Get a single goal",
)
async def get_goal_endpoint(
    goal_id: uuid.UUID,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> GoalResponse:
    goal = await get_goal_by_id(db, user_id=auth.user.id, goal_id=goal_id)
    if goal is None:
        raise AppError(
            404,
            "goal_not_found",
            title="Goal not found",
            detail="That goal does not exist or has already been deleted.",
        )
    progress, milestone_count, completed_count = compute_goal_progress(goal)
    return GoalResponse(
        **serialize_goal_response(goal),
        progress=progress,
        milestone_count=milestone_count,
        completed_milestone_count=completed_count,
    )


@router.patch(
    "/{goal_id}",
    response_model=GoalResponse,
    summary="Update a goal",
)
async def update_goal_endpoint(
    goal_id: uuid.UUID,
    payload: GoalUpdate,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> GoalResponse:
    goal = await update_goal(db, user_id=auth.user.id, goal_id=goal_id, payload=payload)
    if goal is None:
        raise AppError(
            404,
            "goal_not_found",
            title="Goal not found",
            detail="That goal does not exist or has already been deleted.",
        )
    await db.commit()
    await db.refresh(goal, attribute_names=["milestones"])
    progress, milestone_count, completed_count = compute_goal_progress(goal)
    return GoalResponse(
        **serialize_goal_response(goal),
        progress=progress,
        milestone_count=milestone_count,
        completed_milestone_count=completed_count,
    )


@router.delete(
    "/{goal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a goal",
)
async def delete_goal_endpoint(
    goal_id: uuid.UUID,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    goal = await delete_goal(db, user_id=auth.user.id, goal_id=goal_id)
    if goal is None:
        raise AppError(
            404,
            "goal_not_found",
            title="Goal not found",
            detail="That goal does not exist or has already been deleted.",
        )
    await db.commit()
    response.status_code = status.HTTP_204_NO_CONTENT


@router.post(
    "/{goal_id}/restore",
    response_model=GoalResponse,
    summary="Restore a soft-deleted goal",
)
async def restore_goal_endpoint(
    goal_id: uuid.UUID,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> GoalResponse:
    goal = await restore_goal(db, user_id=auth.user.id, goal_id=goal_id)
    if goal is None:
        raise AppError(
            404,
            "goal_not_found",
            title="Goal not found",
            detail="That goal does not exist or has already been deleted.",
        )
    await db.commit()
    await db.refresh(goal, attribute_names=["milestones"])
    progress, milestone_count, completed_count = compute_goal_progress(goal)
    return GoalResponse(
        **serialize_goal_response(goal),
        progress=progress,
        milestone_count=milestone_count,
        completed_milestone_count=completed_count,
    )


# Milestones


@router.post(
    "/{goal_id}/milestones",
    response_model=MilestoneResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a milestone under a goal",
)
async def create_milestone_endpoint(
    goal_id: uuid.UUID,
    payload: MilestoneCreate,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> MilestoneResponse:
    goal = await get_goal_by_id(db, user_id=auth.user.id, goal_id=goal_id)
    if goal is None:
        raise AppError(
            404,
            "goal_not_found",
            title="Goal not found",
            detail="That goal does not exist or has already been deleted.",
        )
    milestone = await create_milestone(db, goal_id=goal_id, payload=payload)
    await db.commit()
    await db.refresh(milestone)
    return MilestoneResponse.model_validate(milestone)


@router.get(
    "/{goal_id}/milestones",
    response_model=MilestoneListResponse,
    summary="List milestones under a goal",
)
async def list_milestones_endpoint(
    goal_id: uuid.UUID,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> MilestoneListResponse:
    goal = await get_goal_by_id(db, user_id=auth.user.id, goal_id=goal_id)
    if goal is None:
        raise AppError(
            404,
            "goal_not_found",
            title="Goal not found",
            detail="That goal does not exist or has already been deleted.",
        )
    milestones = await list_milestones(db, goal_id=goal_id)
    return MilestoneListResponse(
        milestones=[MilestoneResponse.model_validate(m) for m in milestones]
    )


@router.patch(
    "/milestones/{milestone_id}",
    response_model=MilestoneResponse,
    summary="Update a milestone",
)
async def update_milestone_endpoint(
    milestone_id: uuid.UUID,
    payload: MilestoneUpdate,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> MilestoneResponse:
    result = await db.execute(
        select(Milestone)
        .join(Goal, Milestone.goal_id == Goal.id)
        .where(
            Milestone.id == milestone_id,
            Goal.user_id == auth.user.id,
        )
    )
    milestone = result.scalar_one_or_none()
    if milestone is None:
        raise AppError(
            404,
            "milestone_not_found",
            title="Milestone not found",
            detail="That milestone does not exist or its goal is not accessible.",
        )

    updated = await update_milestone(
        db, goal_id=milestone.goal_id, milestone_id=milestone_id, payload=payload
    )
    if updated is None:
        raise AppError(
            404,
            "milestone_not_found",
            title="Milestone not found",
            detail="That milestone does not exist.",
        )
    await db.commit()
    await db.refresh(updated)
    return MilestoneResponse.model_validate(updated)


@router.delete(
    "/milestones/{milestone_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a milestone",
)
async def delete_milestone_endpoint(
    milestone_id: uuid.UUID,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    result = await db.execute(
        select(Milestone)
        .join(Goal, Milestone.goal_id == Goal.id)
        .where(
            Milestone.id == milestone_id,
            Goal.user_id == auth.user.id,
        )
    )
    milestone = result.scalar_one_or_none()
    if milestone is None:
        raise AppError(
            404,
            "milestone_not_found",
            title="Milestone not found",
            detail="That milestone does not exist or its goal is not accessible.",
        )

    deleted = await delete_milestone(db, goal_id=milestone.goal_id, milestone_id=milestone_id)
    if deleted is None:
        raise AppError(
            404,
            "milestone_not_found",
            title="Milestone not found",
            detail="That milestone does not exist.",
        )
    await db.commit()
    response.status_code = status.HTTP_204_NO_CONTENT
