"""Privacy, synchronization & cloud AI models (Phase 6).

Includes AI consent, encrypted provider keys, data export, account deletion,
and audit/security events.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.user import User


class AIConsent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Per-user AI provider consent records."""

    __tablename__ = "ai_consents"
    __table_args__ = (
        CheckConstraint(
            "provider IN ('deterministic', 'ollama', 'cloud')",
            name="ai_consents_provider_check",
        ),
        Index("ix_ai_consents_user_provider", "user_id", "provider", unique=True),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    granted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    policy_version: Mapped[str] = mapped_column(
        String(32), nullable=False, server_default="1.0"
    )

    user: Mapped[User] = relationship("User", back_populates="ai_consents")


class DataExport(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Data export requests for user data portability."""

    __tablename__ = "data_exports"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'completed', 'failed')",
            name="data_exports_status_check",
        ),
        Index("ix_data_exports_user_status", "user_id", "status"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending", server_default="pending"
    )
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(nullable=True)
    record_count: Mapped[int | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship("User", back_populates="data_exports")


class AccountDeletion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Account deletion requests with re-authentication requirement."""

    __tablename__ = "account_deletions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'confirmed', 'completed', 'cancelled')",
            name="account_deletions_status_check",
        ),
        Index("ix_account_deletions_user_status", "user_id", "status"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="pending", server_default="pending"
    )
    confirmation_token: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped[User] = relationship("User", back_populates="account_deletions")


class AuditEvent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Audit/security events for auditing and compliance."""

    __tablename__ = "audit_events"
    __table_args__ = (
        Index("ix_audit_events_user_created", "user_id", "created_at"),
        Index("ix_audit_events_event_type", "event_type", "created_at"),
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)

    user: Mapped[User | None] = relationship("User", back_populates="audit_events")
