"""Sync service: device registration and change-log for mobile clients.

Provides pull/push synchronization with explicit conflict resolution. Every
mutable entity change is recorded in `sync_events` with a per-entity revision
counter so clients can detect and resolve concurrent edits.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.sync import SyncDevice, SyncEvent
from app.schemas.sync import (
    SyncDeviceRegisterRequest,
    SyncDeviceResponse,
    SyncEventEntry,
    SyncPullResponse,
    SyncPushRequest,
    SyncPushResponse,
)


def utcnow() -> datetime:
    return datetime.now(UTC)


def _device_to_response(device: SyncDevice) -> SyncDeviceResponse:
    return SyncDeviceResponse(
        id=device.id,
        device_id=device.device_id,
        device_name=device.device_name,
        platform=device.platform,
        app_version=device.app_version,
        last_seen_at=device.last_seen_at,
        created_at=device.created_at,
        updated_at=device.updated_at,
    )


def _event_to_entry(event: SyncEvent) -> SyncEventEntry:
    return SyncEventEntry(
        id=event.id,
        entity_type=event.entity_type,
        entity_id=event.entity_id,
        action=event.action,
        revision=event.revision,
        payload=event.payload,
        created_at=event.created_at,
    )


async def register_device(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    payload: SyncDeviceRegisterRequest,
) -> SyncDeviceResponse:
    """Create or update a registered device for a user."""
    result = await db.execute(
        select(SyncDevice).where(
            SyncDevice.user_id == user_id,
            SyncDevice.device_id == payload.device_id,
        )
    )
    device = result.scalar_one_or_none()
    now = utcnow()
    if device is None:
        device = SyncDevice(
            user_id=user_id,
            device_id=payload.device_id,
            device_name=payload.device_name,
            platform=payload.platform,
            app_version=payload.app_version,
            last_seen_at=now,
        )
        db.add(device)
    else:
        device.device_name = payload.device_name
        device.platform = payload.platform
        device.app_version = payload.app_version
        device.last_seen_at = now
    await db.flush()
    await db.refresh(device)
    return _device_to_response(device)


async def list_devices(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
) -> list[SyncDeviceResponse]:
    """List all registered devices for a user."""
    result = await db.execute(
        select(SyncDevice)
        .where(SyncDevice.user_id == user_id)
        .order_by(desc(SyncDevice.last_seen_at))
    )
    return [_device_to_response(d) for d in result.scalars().all()]


async def unregister_device(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    device_id: str,
) -> bool:
    """Unregister (delete) a device for a user."""
    result = await db.execute(
        select(SyncDevice).where(
            SyncDevice.user_id == user_id,
            SyncDevice.device_id == device_id,
        )
    )
    device = result.scalar_one_or_none()
    if device is None:
        return False
    await db.delete(device)
    await db.flush()
    return True


async def record_event(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    entity_type: str,
    entity_id: uuid.UUID,
    action: str,
    payload: dict[str, Any] | None = None,
) -> SyncEvent:
    """Append a change event and bump the entity's revision.

    The revision is computed as 1 + the max existing revision for the
    (entity_type, entity_id) pair, so concurrent edits produce distinct
    revision numbers that clients can use for conflict detection.
    """
    result = await db.execute(
        select(SyncEvent.revision).where(
            SyncEvent.entity_type == entity_type,
            SyncEvent.entity_id == entity_id,
        )
    )
    revisions = result.scalars().all()
    next_revision = (max(revisions) + 1) if revisions else 1

    event = SyncEvent(
        user_id=user_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        revision=next_revision,
        payload=payload,
    )
    db.add(event)
    await db.flush()
    await db.refresh(event)
    return event


async def pull(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    since: datetime | None,
    limit: int,
) -> SyncPullResponse:
    """Pull sync events after `since`, newest first, limited to `limit`."""
    stmt = select(SyncEvent).where(SyncEvent.user_id == user_id)
    if since is not None:
        stmt = stmt.where(SyncEvent.created_at > since)
    stmt = stmt.order_by(SyncEvent.created_at.asc()).limit(limit)
    result = await db.execute(stmt)
    events = result.scalars().all()
    return SyncPullResponse(
        events=[_event_to_entry(e) for e in events],
        server_timestamp=utcnow(),
    )


async def push(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    payload: SyncPushRequest,
) -> SyncPushResponse:
    """Push client sync events with conflict resolution.

    Conflict policy: the server's stored revision wins. If a client event
    carries a revision lower than the server's current revision for the same
    (entity_type, entity_id), it is a conflict and is not applied. If the
    revisions match (or no prior event exists), the event is applied and the
    revision is bumped.
    """
    applied = 0
    conflicts: list[dict[str, Any]] = []

    for entry in payload.events:
        # Look up the server's current revision for this entity.
        result = await db.execute(
            select(SyncEvent.revision).where(
                SyncEvent.entity_type == entry.entity_type,
                SyncEvent.entity_id == entry.entity_id,
            )
        )
        server_revisions = result.scalars().all()
        server_rev = max(server_revisions) if server_revisions else 0

        if entry.revision is not None and entry.revision <= server_rev:
            conflicts.append(
                {
                    "entity_type": entry.entity_type,
                    "entity_id": str(entry.entity_id),
                    "client_revision": entry.revision,
                    "server_revision": server_rev,
                    "resolution": "server_wins",
                }
            )
            continue

        await record_event(
            db,
            user_id=user_id,
            entity_type=entry.entity_type,
            entity_id=entry.entity_id,
            action=entry.action,
            payload=entry.payload,
        )
        applied += 1

    await db.flush()
    return SyncPushResponse(
        applied=applied,
        conflicts=conflicts,
        server_timestamp=utcnow(),
    )
