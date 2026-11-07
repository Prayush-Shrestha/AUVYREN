"""Calendar event service: CRUD and range queries."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.calendar import CalendarEvent
from app.schemas.calendar import CalendarEventCreate, CalendarEventUpdate


def utcnow() -> datetime:
    return datetime.now(__import__("datetime").UTC)


async def get_event_by_id(
    db: AsyncSession, *, user_id: uuid.UUID, event_id: uuid.UUID
) -> CalendarEvent | None:
    result = await db.execute(
        select(CalendarEvent).where(
            CalendarEvent.id == event_id, CalendarEvent.user_id == user_id
        )
    )
    return result.scalar_one_or_none()


async def create_event(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    payload: CalendarEventCreate,
) -> CalendarEvent:
    event = CalendarEvent(
        user_id=user_id,
        project_id=payload.project_id,
        title=payload.title,
        description=payload.description,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        all_day=payload.all_day,
        location=payload.location,
    )
    db.add(event)
    await db.flush()
    await db.refresh(event)
    return event


async def update_event(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    event_id: uuid.UUID,
    payload: CalendarEventUpdate,
) -> CalendarEvent | None:
    event = await get_event_by_id(db, user_id=user_id, event_id=event_id)
    if event is None:
        return None

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(event, field, value)

    await db.flush()
    await db.refresh(event)
    return event


async def delete_event(
    db: AsyncSession, *, user_id: uuid.UUID, event_id: uuid.UUID
) -> CalendarEvent | None:
    event = await get_event_by_id(db, user_id=user_id, event_id=event_id)
    if event is None:
        return None
    event.deleted_at = utcnow()
    await db.flush()
    return event


async def restore_event(
    db: AsyncSession, *, user_id: uuid.UUID, event_id: uuid.UUID
) -> CalendarEvent | None:
    event = await get_event_by_id(db, user_id=user_id, event_id=event_id)
    if event is None:
        return None
    event.deleted_at = None
    await db.flush()
    return event


async def list_events(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    starts_after: datetime | None = None,
    ends_before: datetime | None = None,
    include_deleted: bool = False,
    limit: int = 200,
    offset: int = 0,
) -> list[CalendarEvent]:
    query = select(CalendarEvent).where(CalendarEvent.user_id == user_id)

    if not include_deleted:
        query = query.where(CalendarEvent.deleted_at.is_(None))

    if starts_after is not None:
        query = query.where(CalendarEvent.ends_at > starts_after)

    if ends_before is not None:
        query = query.where(CalendarEvent.starts_at < ends_before)

    query = (
        query.order_by(CalendarEvent.starts_at)
        .limit(limit)
        .offset(offset)
    )

    result = await db.execute(query)
    return list(result.scalars().all())
