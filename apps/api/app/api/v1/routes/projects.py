"""Project endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_auth, require_csrf
from app.api.errors import AppError
from app.db.session import get_db_session
from app.schemas.project import (
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
)
from app.services.auth import CurrentAuth
from app.services.project import (
    compute_project_progress,
    create_project,
    delete_project,
    get_project_by_id,
    list_projects,
    restore_project,
    serialize_project_response,
    update_project,
)

router = APIRouter(prefix="/projects", tags=["Projects"], dependencies=[Depends(require_csrf)])


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a project",
)
async def create_project_endpoint(
    payload: ProjectCreate,
    request: Request,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> ProjectResponse:
    project = await create_project(db, user_id=auth.user.id, payload=payload)
    await db.commit()
    await db.refresh(project)
    task_count, completed_count = await compute_project_progress(
        db, user_id=auth.user.id, project_id=project.id
    )
    return ProjectResponse(**serialize_project_response(project, task_count, completed_count))


@router.get(
    "",
    response_model=ProjectListResponse,
    summary="List projects",
)
async def list_projects_endpoint(
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
    status: str | None = Query(None),
    include_deleted: bool = Query(False),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> ProjectListResponse:
    projects = await list_projects(
        db,
        user_id=auth.user.id,
        status=status,
        include_deleted=include_deleted,
        limit=limit,
        offset=offset,
    )
    items = []
    for project in projects:
        task_count, completed_count = await compute_project_progress(
            db, user_id=auth.user.id, project_id=project.id
        )
        items.append(
            ProjectResponse(
                **serialize_project_response(project, task_count, completed_count)
            )
        )
    return ProjectListResponse(projects=items)


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get a single project",
)
async def get_project_endpoint(
    project_id: uuid.UUID,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> ProjectResponse:
    project = await get_project_by_id(db, user_id=auth.user.id, project_id=project_id)
    if project is None:
        raise AppError(
            404,
            "project_not_found",
            title="Project not found",
            detail="That project does not exist or has already been deleted.",
        )
    task_count, completed_count = await compute_project_progress(
        db, user_id=auth.user.id, project_id=project_id
    )
    return ProjectResponse(
        **serialize_project_response(project, task_count, completed_count)
    )


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update a project",
)
async def update_project_endpoint(
    project_id: uuid.UUID,
    payload: ProjectUpdate,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> ProjectResponse:
    project = await update_project(
        db, user_id=auth.user.id, project_id=project_id, payload=payload
    )
    if project is None:
        raise AppError(
            404,
            "project_not_found",
            title="Project not found",
            detail="That project does not exist or has already been deleted.",
        )
    await db.commit()
    await db.refresh(project)
    task_count, completed_count = await compute_project_progress(
        db, user_id=auth.user.id, project_id=project_id
    )
    return ProjectResponse(
        **serialize_project_response(project, task_count, completed_count)
    )


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a project",
)
async def delete_project_endpoint(
    project_id: uuid.UUID,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    project = await delete_project(db, user_id=auth.user.id, project_id=project_id)
    if project is None:
        raise AppError(
            404,
            "project_not_found",
            title="Project not found",
            detail="That project does not exist or has already been deleted.",
        )
    await db.commit()
    response.status_code = status.HTTP_204_NO_CONTENT


@router.post(
    "/{project_id}/restore",
    response_model=ProjectResponse,
    summary="Restore a soft-deleted project",
)
async def restore_project_endpoint(
    project_id: uuid.UUID,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> ProjectResponse:
    project = await restore_project(db, user_id=auth.user.id, project_id=project_id)
    if project is None:
        raise AppError(
            404,
            "project_not_found",
            title="Project not found",
            detail="That project does not exist or has already been deleted.",
        )
    await db.commit()
    await db.refresh(project)
    task_count, completed_count = await compute_project_progress(
        db, user_id=auth.user.id, project_id=project_id
    )
    return ProjectResponse(
        **serialize_project_response(project, task_count, completed_count)
    )
