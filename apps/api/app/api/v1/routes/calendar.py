"""Calendar event endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_auth
from app.api.errors import AppError
from app.db.session import get_db_session
from app.schemas.calendar import (
    CalendarEventCreate,
    CalendarEventListResponse,
    CalendarEventResponse,
    CalendarEventUpdate,
)
from app.services.auth import CurrentAuth
from app.services.calendar import (
    create_event,
    delete_event,
    get_event_by_id,
    list_events,
    restore_event,
    update_event,
)

router = APIRouter(prefix="/calendar", tags=["Calendar"], dependencies=[Depends(require_csrf)])


@router.post(
    "",
    response_model=CalendarEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a calendar event",
)
async def create_event_endpoint(
    payload: CalendarEventCreate,
    request: Request,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> CalendarEventResponse:
    event = await create_event(db, user_id=auth.user.id, payload=payload)
    return CalendarEventResponse.model_validate(event)


@router.get(
    "",
    response_model=CalendarEventListResponse,
    summary="List calendar events in a time range",
)
async def list_events_endpoint(
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
    starts_after: datetime | None = Query(None),
    ends_before: datetime | None = Query(None),
    include_deleted: bool = Query(False),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
) -> CalendarEventListResponse:
    events = await list_events(
        db,
        user_id=auth.user.id,
        starts_after=starts_after,
        ends_before=ends_before,
        include_deleted=include_deleted,
        limit=limit,
        offset=offset,
    )
    return CalendarEventListResponse(
        events=[CalendarEventResponse.model_validate(e) for e in events]
    )


@router.get(
    "/{event_id}",
    response_model=CalendarEventResponse,
    summary="Get a single calendar event",
)
async def get_event_endpoint(
    event_id: uuid.UUID,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> CalendarEventResponse:
    event = await get_event_by_id(db, user_id=auth.user.id, event_id=event_id)
    if event is None:
        raise AppError(
            404,
            "event_not_found",
            title="Event not found",
            detail="That event does not exist or has already been deleted.",
        )
    return CalendarEventResponse.model_validate(event)


@router.patch(
    "/{event_id}",
    response_model=CalendarEventResponse,
    summary="Update a calendar event",
)
async def update_event_endpoint(
    event_id: uuid.UUID,
    payload: CalendarEventUpdate,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> CalendarEventResponse:
    event = await update_event(
        db, user_id=auth.user.id, event_id=event_id, payload=payload
    )
    if event is None:
        raise AppError(
            404,
            "event_not_found",
            title="Event not found",
            detail="That event does not exist or has already been deleted.",
        )
    return CalendarEventResponse.model_validate(event)


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a calendar event",
)
async def delete_event_endpoint(
    event_id: uuid.UUID,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    event = await delete_event(db, user_id=auth.user.id, event_id=event_id)
    if event is None:
        raise AppError(
            404,
            "event_not_found",
            title="Event not found",
            detail="That event does not exist or has already been deleted.",
        )
    response.status_code = status.HTTP_204_NO_CONTENT


@router.post(
    "/{event_id}/restore",
    response_model=CalendarEventResponse,
    summary="Restore a soft-deleted calendar event",
)
async def restore_event_endpoint(
    event_id: uuid.UUID,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> CalendarEventResponse:
    event = await restore_event(db, user_id=auth.user.id, event_id=event_id)
    if event is None:
        raise AppError(
            404,
            "event_not_found",
            title="Event not found",
            detail="That event does not exist or has already been deleted.",
        )
    return CalendarEventResponse.model_validate(event)
