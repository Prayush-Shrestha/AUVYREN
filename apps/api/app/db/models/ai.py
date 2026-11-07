"""AI provider configuration, insights and usage log models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AIProviderConfig(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Per-user AI provider configuration (Phase 4: Ollama; Phase 6: cloud)."""

    __tablename__ = "ai_provider_configs"
    __table_args__ = (
        CheckConstraint(
            "provider IN ('deterministic', 'ollama', 'cloud')",
            name="ai_provider_configs_provider_check",
        ),
        Index("ix_ai_provider_configs_user_provider", "user_id", "provider"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    base_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    encrypted_secret: Mapped[str | None] = mapped_column(Text, nullable=True)
    secret_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_default: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )


class AIInsight(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Generated AI/deterministic insight with provenance."""

    __tablename__ = "ai_insights"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('prioritize', 'review', 'ask', 'plan', 'analyze', 'briefing')",
            name="ai_insights_kind_check",
        ),
        Index("ix_ai_insights_user_kind", "user_id", "kind"),
        Index("ix_ai_insights_user_created", "user_id", "created_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    dismissed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class AIUsageLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Usage metadata for AI requests (tokens, cost, success/failure)."""

    __tablename__ = "ai_usage_logs"
    __table_args__ = (
        Index("ix_ai_usage_logs_user_created", "user_id", "created_at"),
        Index("ix_ai_usage_logs_user_provider", "user_id", "provider"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    request_type: Mapped[str] = mapped_column(String(32), nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tokens_in: Mapped[int | None] = mapped_column(nullable=True)
    tokens_out: Mapped[int | None] = mapped_column(nullable=True)
    estimated_cost: Mapped[float | None] = mapped_column(nullable=True)
    success: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
