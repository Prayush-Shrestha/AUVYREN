"""Import every model so Alembic and SQLAlchemy see the complete metadata."""

from app.db.base import Base
from app.db.models.auth import PasswordResetToken, UserSession
from app.db.models.calendar import CalendarEvent
from app.db.models.enums import (
    GoalStatus,
    HabitSchedule,
    MilestoneStatus,
    ProjectStatus,
    TaskPriority,
    TaskStatus,
)
from app.db.models.goal import Goal
from app.db.models.habit import Habit, HabitLog
from app.db.models.milestone import Milestone
from app.db.models.project import Project
from app.db.models.routine import Routine, RoutineStep
from app.db.models.task import Task
from app.db.models.user import User, UserSettings

__all__ = [
    "Base",
    "CalendarEvent",
    "Goal",
    "GoalStatus",
    "Habit",
    "HabitLog",
    "HabitSchedule",
    "Milestone",
    "MilestoneStatus",
    "PasswordResetToken",
    "Project",
    "ProjectStatus",
    "Routine",
    "RoutineStep",
    "Task",
    "TaskPriority",
    "TaskStatus",
    "User",
    "UserSession",
    "UserSettings",
]
