from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.models.enums import GoalStatus, enum_type

if TYPE_CHECKING:
    from app.db.models.milestone import Milestone


class Goal(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "goals"
    __table_args__ = (
        CheckConstraint(
            "manual_progress IS NULL OR manual_progress BETWEEN 0 AND 100",
            name="manual_progress_range",
        ),
        Index("ix_goals_user_status", "user_id", "status"),
        Index("ix_goals_user_target_date", "user_id", "target_date"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    outcome: Mapped[str | None] = mapped_column(Text)
    status: Mapped[GoalStatus] = mapped_column(
        enum_type(GoalStatus, "goal_status"),
        nullable=False,
        default=GoalStatus.ACTIVE,
        server_default=GoalStatus.ACTIVE.value,
    )
    target_date: Mapped[date | None] = mapped_column(Date)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    manual_progress: Mapped[int | None] = mapped_column(SmallInteger)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    milestones: Mapped[list[Milestone]] = relationship(
        "Milestone",
        back_populates="goal",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Milestone.sort_order",
    )
