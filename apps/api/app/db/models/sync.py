"""Sync models: device registration and change-log for mobile clients.

These tables enable cross-device synchronization for the Phase 8 mobile
application. Every mutable entity change is recorded in `sync_events` so
clients can pull incremental updates and push local changes with explicit
conflict resolution.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.user import User


class SyncDevice(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A registered client device for a user's account."""

    __tablename__ = "sync_devices"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    device_id: Mapped[str] = mapped_column(String(255), nullable=False)
    device_name: Mapped[str | None] = mapped_column(String(255))
    platform: Mapped[str | None] = mapped_column(String(32))
    app_version: Mapped[str | None] = mapped_column(String(64))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index("uq_sync_devices_user_device", "user_id", "device_id", unique=True),
    )

    user: Mapped[User] = relationship("User", back_populates="sync_devices")


class SyncEvent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """One change to a user-owned entity, for incremental sync.

    `revision` is a per-entity monotonic counter so clients can detect
    concurrent edits and resolve conflicts deterministically.
    """

    __tablename__ = "sync_events"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    action: Mapped[str] = mapped_column(String(16), nullable=False)
    revision: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default=text("1")
    )
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    __table_args__ = (
        Index("ix_sync_events_user_type_created", "user_id", "entity_type", "created_at"),
        Index(
            "uq_sync_events_entity_revision",
            "entity_type",
            "entity_id",
            "revision",
            unique=True,
        ),
    )

    user: Mapped[User] = relationship("User", back_populates="sync_events")
