import uuid
from datetime import UTC, date, datetime, timedelta

from app.db.models import (
    CalendarEvent,
    Goal,
    Habit,
    HabitLog,
    Milestone,
    Project,
    Task,
    User,
    UserSettings,
)
from app.db.models.enums import TaskPriority, TaskStatus
from app.db.session import SessionFactory
from sqlalchemy import select


async def test_core_records_round_trip_and_cascade() -> None:
    email = f"schema-test-{uuid.uuid4().hex}@auvyren.local"

    async with SessionFactory() as session:
        user = User(email=email, password_hash="test-hash", full_name="Schema Test")
        session.add(user)
        await session.flush()

        session.add(UserSettings(user_id=user.id, timezone="Asia/Kathmandu"))
        project = Project(user_id=user.id, name="Foundation")
        goal = Goal(user_id=user.id, title="Ship Phase 0", outcome="Verified schema")
        session.add_all([project, goal])
        await session.flush()

        task = Task(
            user_id=user.id,
            project_id=project.id,
            title="Run migrations",
            status=TaskStatus.IN_PROGRESS,
            priority=TaskPriority.HIGH,
            planned_for=date.today(),
            due_at=datetime.now(UTC) + timedelta(days=1),
        )
        milestone = Milestone(goal_id=goal.id, title="Database online")
        habit = Habit(user_id=user.id, name="Daily review", schedule="daily")
        session.add_all([task, milestone, habit])
        await session.flush()

        session.add(HabitLog(habit_id=habit.id, user_id=user.id, log_date=date.today()))
        session.add(
            CalendarEvent(
                user_id=user.id,
                project_id=project.id,
                title="Planning",
                starts_at=datetime.now(UTC),
                ends_at=datetime.now(UTC) + timedelta(hours=1),
            )
        )
        await session.flush()

        assert task.status is TaskStatus.IN_PROGRESS
        assert task.priority is TaskPriority.HIGH
        assert task.id is not None

        stored = await session.scalar(select(User).where(User.email == email))
        assert stored is not None

        # Account deletion cascades to every owned record.
        await session.delete(stored)
        await session.flush()

        assert await session.scalar(select(Task).where(Task.user_id == user.id)) is None
        assert await session.scalar(select(Project).where(Project.user_id == user.id)) is None
        assert await session.scalar(select(Goal).where(Goal.user_id == user.id)) is None
        assert await session.scalar(select(Habit).where(Habit.user_id == user.id)) is None
        assert (
            await session.scalar(select(CalendarEvent).where(CalendarEvent.user_id == user.id))
            is None
        )

        await session.rollback()


async def test_updated_at_trigger_uses_database_clock() -> None:
    async with SessionFactory() as session:
        user = User(
            email=f"trigger-test-{uuid.uuid4().hex}@auvyren.local",
            password_hash="test-hash",
        )
        session.add(user)
        await session.flush()
        original_updated_at = user.updated_at

        user.full_name = "Updated"
        await session.flush()
        await session.refresh(user)

        assert user.updated_at > original_updated_at

        await session.rollback()
