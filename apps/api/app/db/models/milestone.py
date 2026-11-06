from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.models.enums import MilestoneStatus, enum_type
from app.db.models.goal import Goal


class Milestone(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "milestones"
    __table_args__ = (Index("ix_milestones_goal_sort", "goal_id", "sort_order"),)

    goal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("goals.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[MilestoneStatus] = mapped_column(
        enum_type(MilestoneStatus, "milestone_status"),
        nullable=False,
        default=MilestoneStatus.PENDING,
        server_default=MilestoneStatus.PENDING.value,
    )
    target_date: Mapped[date | None] = mapped_column(Date)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))

    goal: Mapped[Goal] = relationship("Goal", back_populates="milestones")
