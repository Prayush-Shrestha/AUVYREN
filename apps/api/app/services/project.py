"""Project service: CRUD, task association, progress computation."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.project import Project
from app.db.models.task import Task
from app.schemas.project import ProjectCreate, ProjectUpdate


def utcnow() -> datetime:
    return datetime.now(__import__("datetime").UTC)


async def get_project_by_id(
    db: AsyncSession, *, user_id: uuid.UUID, project_id: uuid.UUID
) -> Project | None:
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def create_project(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    payload: ProjectCreate,
) -> Project:
    project = Project(
        user_id=user_id,
        name=payload.name,
        description=payload.description,
        status=payload.status,
        start_date=payload.start_date,
        due_date=payload.due_date,
    )
    db.add(project)
    await db.flush()
    await db.refresh(project)
    return project


async def update_project(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    project_id: uuid.UUID,
    payload: ProjectUpdate,
) -> Project | None:
    project = await get_project_by_id(db, user_id=user_id, project_id=project_id)
    if project is None:
        return None

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(project, field, value)

    await db.flush()
    await db.refresh(project)
    return project


async def delete_project(
    db: AsyncSession, *, user_id: uuid.UUID, project_id: uuid.UUID
) -> Project | None:
    project = await get_project_by_id(db, user_id=user_id, project_id=project_id)
    if project is None:
        return None
    project.deleted_at = utcnow()
    await db.flush()
    return project


async def restore_project(
    db: AsyncSession, *, user_id: uuid.UUID, project_id: uuid.UUID
) -> Project | None:
    project = await get_project_by_id(db, user_id=user_id, project_id=project_id)
    if project is None:
        return None
    project.deleted_at = None
    await db.flush()
    return project


async def list_projects(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    status: str | None = None,
    include_deleted: bool = False,
    limit: int = 100,
    offset: int = 0,
) -> list[Project]:
    query = select(Project).where(Project.user_id == user_id)

    if not include_deleted:
        query = query.where(Project.deleted_at.is_(None))

    if status is not None:
        query = query.where(Project.status == status)

    query = query.order_by(Project.created_at.desc()).limit(limit).offset(offset)

    result = await db.execute(query)
    return list(result.scalars().all())


async def compute_project_progress(
    db: AsyncSession, *, user_id: uuid.UUID, project_id: uuid.UUID
) -> tuple[int, int]:
    """Return (task_count, completed_task_count)."""
    project_id = uuid.UUID(project_id) if isinstance(project_id, str) else project_id
    result = await db.execute(
        select(Task.id, Task.status).where(
            Task.user_id == user_id,
            Task.project_id == project_id,
            Task.deleted_at.is_(None),
        )
    )
    task_count = 0
    completed_count = 0
    for row in result.all():
        task_count += 1
        if str(row[1]) == "done":
            completed_count += 1
    return task_count, completed_count


def serialize_project_response(
    project: Project, task_count: int, completed_task_count: int
) -> dict:
    return {
        "id": project.id,
        "user_id": project.user_id,
        "name": project.name,
        "description": project.description,
        "status": project.status,
        "start_date": project.start_date,
        "due_date": project.due_date,
        "deleted_at": project.deleted_at,
        "task_count": task_count,
        "completed_task_count": completed_task_count,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
    }
