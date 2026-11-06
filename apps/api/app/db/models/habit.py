from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.models.enums import HabitSchedule, enum_type

if TYPE_CHECKING:
    from app.db.models.habit import HabitLog


class Habit(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "habits"
    __table_args__ = (
        CheckConstraint(
            "(schedule = 'daily' AND target_per_week IS NULL) "
            "OR (schedule = 'weekly' AND target_per_week BETWEEN 1 AND 7)",
            name="schedule_target_consistent",
        ),
        Index("ix_habits_user_archived", "user_id", "is_archived"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    schedule: Mapped[HabitSchedule] = mapped_column(
        enum_type(HabitSchedule, "habit_schedule"),
        nullable=False,
        default=HabitSchedule.DAILY,
        server_default=HabitSchedule.DAILY.value,
    )
    target_per_week: Mapped[int | None] = mapped_column(SmallInteger)
    start_date: Mapped[date] = mapped_column(
        Date, nullable=False, server_default=func.current_date()
    )
    is_archived: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )

    logs: Mapped[list[HabitLog]] = relationship(
        "HabitLog",
        back_populates="habit",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="HabitLog.log_date",
    )


class HabitLog(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "habit_logs"
    __table_args__ = (
        UniqueConstraint("habit_id", "log_date", name="habit_log_date"),
        Index("ix_habit_logs_user_date", "user_id", "log_date"),
    )

    habit_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("habits.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    log_date: Mapped[date] = mapped_column(Date, nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    habit: Mapped[Habit] = relationship("Habit", back_populates="logs")
