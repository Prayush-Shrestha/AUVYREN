"""Domain enumerations stored as constrained strings (not native PG enums)."""

from enum import Enum as PyEnum
from enum import StrEnum

from sqlalchemy import Enum


def enum_type(enum_cls: type[PyEnum], name: str) -> Enum:
    """Store the lowercase enum *value*, never the Python member name."""
    return Enum(
        enum_cls,
        name=name,
        native_enum=False,
        length=20,
        create_constraint=True,
        validate_strings=True,
        values_callable=lambda members: [str(member.value) for member in members],
    )


class ProjectStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class TaskStatus(StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"


class TaskPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class GoalStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class MilestoneStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"


class HabitSchedule(StrEnum):
    DAILY = "daily"
    WEEKLY = "weekly"
