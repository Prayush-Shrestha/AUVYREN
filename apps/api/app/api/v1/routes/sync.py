"""Sync endpoints: device registration and incremental change-log pull/push."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_auth, require_csrf
from app.api.errors import AppError
from app.db.session import get_db_session
from app.schemas.sync import (
    SyncDeviceRegisterRequest,
    SyncDeviceResponse,
    SyncPullResponse,
    SyncPushRequest,
    SyncPushResponse,
)
from app.services.auth import CurrentAuth
from app.services.sync import (
    list_devices,
    pull,
    push,
    register_device,
    unregister_device,
)

router = APIRouter(prefix="/sync", tags=["Sync"], dependencies=[Depends(require_csrf)])


def _parse_since(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError as err:
        raise AppError(
            400,
            "invalid_since",
            title="Invalid since parameter",
            detail="`since` must be an ISO 8601 timestamp.",
        ) from err


@router.get(
    "/status",
    response_model=SyncPullResponse,
    summary="Sync status and pending events since a timestamp",
)
async def sync_status(
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
    since: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
) -> SyncPullResponse:
    return await pull(
        db,
        user_id=auth.user.id,
        since=_parse_since(since),
        limit=limit,
    )


@router.get(
    "/devices",
    response_model=list[SyncDeviceResponse],
    summary="List registered sync devices",
)
async def list_devices_endpoint(
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> list[SyncDeviceResponse]:
    return await list_devices(db, user_id=auth.user.id)


@router.post(
    "/devices",
    response_model=SyncDeviceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a sync device",
)
async def register_device_endpoint(
    payload: SyncDeviceRegisterRequest,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> SyncDeviceResponse:
    device = await register_device(db, user_id=auth.user.id, payload=payload)
    await db.commit()
    return device


@router.delete(
    "/devices/{device_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unregister a sync device",
)
async def unregister_device_endpoint(
    device_id: str,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    removed = await unregister_device(db, user_id=auth.user.id, device_id=device_id)
    if not removed:
        raise AppError(
            404,
            "device_not_found",
            title="Device not found",
            detail="That sync device does not exist or is not registered to your account.",
        )
    await db.commit()
    response.status_code = status.HTTP_204_NO_CONTENT


@router.get(
    "/pull",
    response_model=SyncPullResponse,
    summary="Pull incremental sync events",
)
async def sync_pull(
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
    since: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
) -> SyncPullResponse:
    return await pull(
        db,
        user_id=auth.user.id,
        since=_parse_since(since),
        limit=limit,
    )


@router.post(
    "/push",
    response_model=SyncPushResponse,
    summary="Push local sync events with conflict resolution",
)
async def sync_push(
    payload: SyncPushRequest,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> SyncPushResponse:
    result = await push(db, user_id=auth.user.id, payload=payload)
    await db.commit()
    return result
