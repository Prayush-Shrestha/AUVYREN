from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.routine import RoutineStep


class Routine(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "routines"
    __table_args__ = (Index("ix_routines_user_active", "user_id", "is_active"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    time_of_day: Mapped[str | None] = mapped_column(String(32))
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )

    steps: Mapped[list[RoutineStep]] = relationship(
        "RoutineStep",
        back_populates="routine",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="RoutineStep.sort_order",
    )


class RoutineStep(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "routine_steps"
    __table_args__ = (
        CheckConstraint(
            "duration_minutes IS NULL OR (duration_minutes > 0 AND duration_minutes <= 1440)",
            name="duration_minutes_range",
        ),
        Index("ix_routine_steps_routine_sort", "routine_id", "sort_order"),
    )

    routine_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("routines.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    duration_minutes: Mapped[int | None] = mapped_column(SmallInteger)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))

    routine: Mapped[Routine] = relationship("Routine", back_populates="steps")
