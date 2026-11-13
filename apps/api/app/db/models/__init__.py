"""Import every model so Alembic and SQLAlchemy see the complete metadata."""

from app.db.base import Base
from app.db.models.ai import AIInsight, AIProviderConfig, AIUsageLog
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
from app.db.models.knowledge import Note, NoteKind, NoteLink, NoteSourceType
from app.db.models.milestone import Milestone
from app.db.models.privacy import AccountDeletion, AIConsent, AuditEvent, DataExport
from app.db.models.project import Project
from app.db.models.routine import Routine, RoutineStep
from app.db.models.task import Task
from app.db.models.user import User, UserSettings

__all__ = [
    "AIInsight",
    "AIProviderConfig",
    "AIUsageLog",
    "AIConsent",
    "AccountDeletion",
    "AuditEvent",
    "Base",
    "CalendarEvent",
    "DataExport",
    "Goal",
    "GoalStatus",
    "Habit",
    "HabitLog",
    "HabitSchedule",
    "Milestone",
    "MilestoneStatus",
    "Note",
    "NoteLink",
    "NoteKind",
    "NoteSourceType",
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
