"""Task endpoints: CRUD, completion, filtering."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_auth, require_csrf
from app.api.errors import AppError
from app.db.session import get_db_session
from app.schemas.task import (
    TaskCreate,
    TaskListResponse,
    TaskResponse,
    TaskStatusUpdate,
    TaskUpdate,
)
from app.services.auth import CurrentAuth
from app.services.task import (
    count_tasks,
    create_task,
    delete_task,
    get_task_by_id,
    get_today_tasks,
    get_upcoming_tasks,
    list_tasks,
    restore_task,
    search_tasks,
    update_task,
)

router = APIRouter(prefix="/tasks", tags=["Tasks"], dependencies=[Depends(require_csrf)])


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a task",
)
async def create_task_endpoint(
    payload: TaskCreate,
    request: Request,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> TaskResponse:
    task = await create_task(db, user_id=auth.user.id, payload=payload)
    await db.commit()
    await db.refresh(task)
    return TaskResponse.model_validate(task)


@router.get(
    "",
    response_model=TaskListResponse,
    summary="List tasks with optional filters",
)
async def list_tasks_endpoint(
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
    status: str | None = Query(None),
    project_id: uuid.UUID | None = Query(None),
    category: str | None = Query(None),
    planned_for: date | None = Query(None),
    due_before: datetime | None = Query(None),
    include_deleted: bool = Query(False),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> TaskListResponse:
    tasks = await list_tasks(
        db,
        user_id=auth.user.id,
        status=status,
        project_id=project_id,
        category=category,
        planned_for=planned_for,
        due_before=due_before,
        include_deleted=include_deleted,
        limit=limit,
        offset=offset,
    )
    total = await count_tasks(
        db,
        user_id=auth.user.id,
        status=status,
        project_id=project_id,
        category=category,
        planned_for=planned_for,
        due_before=due_before,
        include_deleted=include_deleted,
    )
    response.headers["X-Total-Count"] = str(total)
    return TaskListResponse(tasks=[TaskResponse.model_validate(t) for t in tasks])


@router.get(
    "/today",
    response_model=TaskListResponse,
    summary="Tasks due or planned for today",
)
async def today_tasks_endpoint(
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
    target_date: date | None = Query(None),
) -> TaskListResponse:
    tasks = await get_today_tasks(db, user_id=auth.user.id, target_date=target_date)
    return TaskListResponse(tasks=[TaskResponse.model_validate(t) for t in tasks])


@router.get(
    "/upcoming",
    response_model=TaskListResponse,
    summary="Upcoming tasks within a window",
)
async def upcoming_tasks_endpoint(
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(20, ge=1, le=100),
) -> TaskListResponse:
    tasks = await get_upcoming_tasks(db, user_id=auth.user.id, days=days, limit=limit)
    return TaskListResponse(tasks=[TaskResponse.model_validate(t) for t in tasks])


@router.get(
    "/search",
    response_model=TaskListResponse,
    summary="Search tasks by title or category",
)
async def search_tasks_endpoint(
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
    q: str = Query(..., min_length=1, max_length=240),
    limit: int = Query(50, ge=1, le=200),
) -> TaskListResponse:
    tasks = await search_tasks(db, user_id=auth.user.id, query_text=q, limit=limit)
    return TaskListResponse(tasks=[TaskResponse.model_validate(t) for t in tasks])


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get a single task",
)
async def get_task_endpoint(
    task_id: uuid.UUID,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> TaskResponse:
    task = await get_task_by_id(db, user_id=auth.user.id, task_id=task_id)
    if task is None:
        raise AppError(
            404,
            "task_not_found",
            title="Task not found",
            detail="That task does not exist or has already been deleted.",
        )
    return TaskResponse.model_validate(task)


@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update a task",
)
async def update_task_endpoint(
    task_id: uuid.UUID,
    payload: TaskUpdate,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> TaskResponse:
    task = await update_task(db, user_id=auth.user.id, task_id=task_id, payload=payload)
    if task is None:
        raise AppError(
            404,
            "task_not_found",
            title="Task not found",
            detail="That task does not exist or has already been deleted.",
        )
    await db.commit()
    await db.refresh(task)
    return TaskResponse.model_validate(task)


@router.patch(
    "/{task_id}/status",
    response_model=TaskResponse,
    summary="Update task status (complete/reopen)",
)
async def update_task_status_endpoint(
    task_id: uuid.UUID,
    payload: TaskStatusUpdate,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> TaskResponse:
    task = await update_task(
        db,
        user_id=auth.user.id,
        task_id=task_id,
        payload=TaskUpdate(status=payload.status),
    )
    if task is None:
        raise AppError(
            404,
            "task_not_found",
            title="Task not found",
            detail="That task does not exist or has already been deleted.",
        )
    await db.commit()
    await db.refresh(task)
    return TaskResponse.model_validate(task)


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a task",
)
async def delete_task_endpoint(
    task_id: uuid.UUID,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    task = await delete_task(db, user_id=auth.user.id, task_id=task_id)
    if task is None:
        raise AppError(
            404,
            "task_not_found",
            title="Task not found",
            detail="That task does not exist or has already been deleted.",
        )
    await db.commit()
    response.status_code = status.HTTP_204_NO_CONTENT


@router.post(
    "/{task_id}/restore",
    response_model=TaskResponse,
    summary="Restore a soft-deleted task",
)
async def restore_task_endpoint(
    task_id: uuid.UUID,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> TaskResponse:
    task = await restore_task(db, user_id=auth.user.id, task_id=task_id)
    if task is None:
        raise AppError(
            404,
            "task_not_found",
            title="Task not found",
            detail="That task does not exist or has already been deleted.",
        )
    await db.commit()
    await db.refresh(task)
    return TaskResponse.model_validate(task)
