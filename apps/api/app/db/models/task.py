from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
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
from app.db.models.enums import TaskPriority, TaskStatus, enum_type
from app.db.models.project import Project


class Task(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint(
            "estimated_minutes IS NULL OR estimated_minutes > 0",
            name="estimated_minutes_positive",
        ),
        Index("ix_tasks_user_status", "user_id", "status"),
        Index("ix_tasks_user_planned_for", "user_id", "planned_for"),
        Index("ix_tasks_user_due_at", "user_id", "due_at"),
        Index("ix_tasks_project_id", "project_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[TaskStatus] = mapped_column(
        enum_type(TaskStatus, "task_status"),
        nullable=False,
        default=TaskStatus.TODO,
        server_default=TaskStatus.TODO.value,
    )
    priority: Mapped[TaskPriority] = mapped_column(
        enum_type(TaskPriority, "task_priority"),
        nullable=False,
        default=TaskPriority.MEDIUM,
        server_default=TaskPriority.MEDIUM.value,
    )
    category: Mapped[str | None] = mapped_column(String(64))
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    planned_for: Mapped[date | None] = mapped_column(Date)
    estimated_minutes: Mapped[int | None] = mapped_column(SmallInteger)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    project: Mapped[Project | None] = relationship("Project", back_populates="tasks")
