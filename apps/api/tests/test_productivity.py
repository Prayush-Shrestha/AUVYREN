from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.db.models import User
from app.db.session import SessionFactory
from app.intelligence.deterministic import (
    daily_plan,
    detect_patterns,
    goal_progress,
    habit_consistency,
    prioritize_tasks,
)
from app.main import app
from httpx import ASGITransport, AsyncClient
from sqlalchemy import update

ORIGIN = "http://localhost:3000"
EMAIL_DOMAIN = "phase3.auvyren.app"
PASSWORD = "correct horse battery staple"


def unique_email(prefix: str = "user") -> str:
    return f"{prefix}-{uuid.uuid4().hex}@{EMAIL_DOMAIN}"


def make_client(*, origin: str | None = ORIGIN) -> AsyncClient:
    headers = {"Origin": origin, "Referer": f"{origin}/"} if origin else {}
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
        headers=headers,
    )


def csrf_headers(token: str) -> dict[str, str]:
    return {"X-CSRF-Token": token}


async def get_csrf(client: AsyncClient) -> str:
    response = await client.get("/api/v1/auth/csrf")
    assert response.status_code == 200, response.text
    return response.json()["csrf_token"]


async def register(
    client: AsyncClient,
    *,
    email: str | None = None,
    password: str = PASSWORD,
    full_name: str | None = "Phase Three",
) -> AsyncClient:
    token = await get_csrf(client)
    return await client.post(
        "/api/v1/auth/register",
        json={"email": email or unique_email(), "password": password, "full_name": full_name},
        headers=csrf_headers(token),
    )


async def login(client: AsyncClient, email: str, password: str):
    token = await get_csrf(client)
    return await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
        headers=csrf_headers(token),
    )


async def auth_headers(client: AsyncClient) -> dict[str, str]:
    return csrf_headers(await get_csrf(client))


async def test_task_crud_and_ownership(client: AsyncClient) -> None:
    email = unique_email("task")
    created = await register(client, email=email)
    assert created.status_code == 201
    headers = await auth_headers(client)

    response = await client.post(
        "/api/v1/tasks",
        json={
            "title": "Review quarterly goals",
            "description": "Look at Q3 outcomes and set Q4 targets.",
            "priority": "high",
            "category": "work",
            "estimated_minutes": 45,
            "sort_order": 1,
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    task = response.json()
    assert task["title"] == "Review quarterly goals"
    assert task["status"] == "todo"
    assert task["priority"] == "high"
    assert task["category"] == "work"
    assert task["estimated_minutes"] == 45

    task_id = task["id"]

    listed = await client.get("/api/v1/tasks", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()["tasks"]) == 1

    fetched = await client.get(f"/api/v1/tasks/{task_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["id"] == task_id

    updated = await client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"title": "Review annual goals", "priority": "urgent"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Review annual goals"
    assert updated.json()["priority"] == "urgent"

    completed = await client.patch(
        f"/api/v1/tasks/{task_id}/status",
        json={"status": "done"},
        headers=headers,
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "done"
    assert completed.json()["completed_at"] is not None

    reopened = await client.patch(
        f"/api/v1/tasks/{task_id}/status",
        json={"status": "todo"},
        headers=headers,
    )
    assert reopened.status_code == 200
    assert reopened.json()["status"] == "todo"
    assert reopened.json()["completed_at"] is None

    deleted = await client.delete(f"/api/v1/tasks/{task_id}", headers=headers)
    assert deleted.status_code == 204

    listed_after = await client.get("/api/v1/tasks", headers=headers)
    assert len(listed_after.json()["tasks"]) == 0

    gone = await client.get(f"/api/v1/tasks/{task_id}", headers=headers)
    assert gone.status_code == 404

    restored = await client.post(f"/api/v1/tasks/{task_id}/restore", headers=headers)
    assert restored.status_code == 200
    assert restored.json()["deleted_at"] is None

    async with make_client() as stranger:
        stranger_created = await register(stranger)
        assert stranger_created.status_code == 201
        stranger_headers = await auth_headers(stranger)

        cross_get = await stranger.get(f"/api/v1/tasks/{task_id}", headers=stranger_headers)
        assert cross_get.status_code == 404

        cross_patch = await stranger.patch(
            f"/api/v1/tasks/{task_id}",
            json={"title": "hacked"},
            headers=stranger_headers,
        )
        assert cross_patch.status_code == 404

        cross_delete = await stranger.delete(f"/api/v1/tasks/{task_id}", headers=stranger_headers)
        assert cross_delete.status_code == 404


async def test_task_filtering_and_search(client: AsyncClient) -> None:
    email = unique_email("filter")
    created = await register(client, email=email)
    assert created.status_code == 201
    headers = await auth_headers(client)

    today = date.today()
    tomorrow = today + timedelta(days=1)

    await client.post(
        "/api/v1/tasks",
        json={
            "title": "Work task",
            "category": "work",
            "status": "todo",
            "planned_for": today.isoformat(),
        },
        headers=headers,
    )
    await client.post(
        "/api/v1/tasks",
        json={
            "title": "Personal task",
            "category": "personal",
            "status": "done",
            "planned_for": tomorrow.isoformat(),
        },
        headers=headers,
    )
    await client.post(
        "/api/v1/tasks",
        json={
            "title": "Work follow-up",
            "category": "work",
            "status": "in_progress",
            "planned_for": today.isoformat(),
        },
        headers=headers,
    )

    todo = await client.get("/api/v1/tasks?category=work", headers=headers)
    assert todo.status_code == 200
    titles = [t["title"] for t in todo.json()["tasks"]]
    assert len(todo.json()["tasks"]) == 2
    assert "Work task" in titles
    assert "Work follow-up" in titles

    work = await client.get("/api/v1/tasks?category=work", headers=headers)
    assert work.status_code == 200
    assert len(work.json()["tasks"]) == 2

    search = await client.get("/api/v1/tasks/search?q=follow-up", headers=headers)
    assert search.status_code == 200
    assert len(search.json()["tasks"]) == 1
    assert search.json()["tasks"][0]["title"] == "Work follow-up"

    planned = await client.get(f"/api/v1/tasks?planned_for={today.isoformat()}", headers=headers)
    assert planned.status_code == 200
    assert len(planned.json()["tasks"]) == 2


async def test_task_upcoming_and_today(client: AsyncClient) -> None:
    email = unique_email("upcoming")
    created = await register(client, email=email)
    assert created.status_code == 201
    headers = await auth_headers(client)

    today = date.today()
    future = today + timedelta(days=3)

    await client.post(
        "/api/v1/tasks",
        json={
            "title": "Due today",
            "due_at": datetime(
                today.year, today.month, today.day, 10, 0, tzinfo=ZoneInfo("UTC")
            ).isoformat(),
            "status": "todo",
        },
        headers=headers,
    )
    await client.post(
        "/api/v1/tasks",
        json={
            "title": "Due in 3 days",
            "due_at": datetime(
                future.year, future.month, future.day, 10, 0, tzinfo=ZoneInfo("UTC")
            ).isoformat(),
            "status": "todo",
        },
        headers=headers,
    )
    await client.post(
        "/api/v1/tasks",
        json={
            "title": "Already done",
            "due_at": datetime(
                today.year, today.month, today.day, 10, 0, tzinfo=ZoneInfo("UTC")
            ).isoformat(),
            "status": "done",
        },
        headers=headers,
    )

    today_resp = await client.get("/api/v1/tasks/today", headers=headers)
    assert today_resp.status_code == 200
    titles = [t["title"] for t in today_resp.json()["tasks"]]
    assert "Due today" in titles

    upcoming = await client.get("/api/v1/tasks/upcoming?days=7", headers=headers)
    assert upcoming.status_code == 200
    upcoming_titles = [t["title"] for t in upcoming.json()["tasks"]]
    assert "Due in 3 days" in upcoming_titles


async def test_task_validation_errors(client: AsyncClient) -> None:
    email = unique_email("validate")
    created = await register(client, email=email)
    assert created.status_code == 201
    headers = await auth_headers(client)

    response = await client.post(
        "/api/v1/tasks",
        json={"title": ""},
        headers=headers,
    )
    assert response.status_code == 422
    assert response.json()["code"] == "request_validation_failed"

    response = await client.post(
        "/api/v1/tasks",
        json={"title": "x" * 241},
        headers=headers,
    )
    assert response.status_code == 422

    response = await client.post(
        "/api/v1/tasks",
        json={"title": "Valid title", "estimated_minutes": -5},
        headers=headers,
    )
    assert response.status_code == 422

    response = await client.post(
        "/api/v1/tasks",
        json={"title": "Valid title", "priority": "critical"},
        headers=headers,
    )
    assert response.status_code == 422


async def test_goal_crud_milestones_and_progress(client: AsyncClient) -> None:
    email = unique_email("goal")
    created = await register(client, email=email)
    assert created.status_code == 201
    headers = await auth_headers(client)

    response = await client.post(
        "/api/v1/goals",
        json={
            "title": "Run a marathon",
            "outcome": "Complete 42.2km under 4 hours",
            "target_date": (date.today() + timedelta(days=90)).isoformat(),
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    goal = response.json()
    goal_id = goal["id"]
    assert goal["progress"] == 0
    assert goal["milestone_count"] == 0
    assert goal["completed_milestone_count"] == 0

    m1 = await client.post(
        f"/api/v1/goals/{goal_id}/milestones",
        json={"title": "Run 5km", "sort_order": 1},
        headers=headers,
    )
    assert m1.status_code == 201
    milestone_id = m1.json()["id"]

    m2 = await client.post(
        f"/api/v1/goals/{goal_id}/milestones",
        json={"title": "Run 10km", "sort_order": 2},
        headers=headers,
    )
    assert m2.status_code == 201

    fetched = await client.get(f"/api/v1/goals/{goal_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["milestone_count"] == 2
    assert fetched.json()["progress"] == 0

    completed_m1 = await client.patch(
        f"/api/v1/goals/milestones/{milestone_id}",
        json={"status": "completed"},
        headers=headers,
    )
    assert completed_m1.status_code == 200
    assert completed_m1.json()["status"] == "completed"
    assert completed_m1.json()["completed_at"] is not None

    fetched = await client.get(f"/api/v1/goals/{goal_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["completed_milestone_count"] == 1
    assert fetched.json()["progress"] == 50

    listed = await client.get(f"/api/v1/goals/{goal_id}/milestones", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()["milestones"]) == 2

    deleted = await client.delete(f"/api/v1/goals/milestones/{milestone_id}", headers=headers)
    assert deleted.status_code == 204

    async with make_client() as stranger:
        stranger_created = await register(stranger)
        assert stranger_created.status_code == 201
        stranger_headers = await auth_headers(stranger)

        cross = await stranger.patch(
            f"/api/v1/goals/milestones/{milestone_id}",
            json={"status": "pending"},
            headers=stranger_headers,
        )
        assert cross.status_code == 404

        cross_delete = await stranger.delete(
            f"/api/v1/goals/milestones/{milestone_id}", headers=stranger_headers
        )
        assert cross_delete.status_code == 404


async def test_goal_cross_user_404(client: AsyncClient) -> None:
    email = unique_email("goal-cross")
    created = await register(client, email=email)
    assert created.status_code == 201
    headers = await auth_headers(client)

    goal = await client.post(
        "/api/v1/goals",
        json={"title": "Private goal"},
        headers=headers,
    )
    assert goal.status_code == 201
    goal_id = goal.json()["id"]

    async with make_client() as stranger:
        stranger_created = await register(stranger)
        assert stranger_created.status_code == 201
        stranger_headers = await auth_headers(stranger)

        cross_get = await stranger.get(f"/api/v1/goals/{goal_id}", headers=stranger_headers)
        assert cross_get.status_code == 404

        cross_patch = await stranger.patch(
            f"/api/v1/goals/{goal_id}",
            json={"title": "hacked"},
            headers=stranger_headers,
        )
        assert cross_patch.status_code == 404

        cross_delete = await stranger.delete(f"/api/v1/goals/{goal_id}", headers=stranger_headers)
        assert cross_delete.status_code == 404

        cross_milestone = await stranger.post(
            f"/api/v1/goals/{goal_id}/milestones",
            json={"title": "hacked milestone"},
            headers=stranger_headers,
        )
        assert cross_milestone.status_code == 404


async def test_project_crud_and_task_association(client: AsyncClient) -> None:
    email = unique_email("project")
    created = await register(client, email=email)
    assert created.status_code == 201
    headers = await auth_headers(client)

    response = await client.post(
        "/api/v1/projects",
        json={
            "name": "Website redesign",
            "description": "Refresh the marketing site",
            "status": "active",
            "start_date": date.today().isoformat(),
            "due_date": (date.today() + timedelta(days=30)).isoformat(),
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    project = response.json()
    project_id = project["id"]
    assert project["task_count"] == 0
    assert project["completed_task_count"] == 0

    task = await client.post(
        "/api/v1/tasks",
        json={
            "title": "Design homepage",
            "project_id": project_id,
            "status": "done",
        },
        headers=headers,
    )
    assert task.status_code == 201

    fetched = await client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["task_count"] == 1

    async with make_client() as stranger:
        stranger_created = await register(stranger)
        assert stranger_created.status_code == 201
        stranger_headers = await auth_headers(stranger)

        cross = await stranger.get(f"/api/v1/projects/{project_id}", headers=stranger_headers)
        assert cross.status_code == 404

        cross_delete = await stranger.delete(
            f"/api/v1/projects/{project_id}", headers=stranger_headers
        )
        assert cross_delete.status_code == 404


async def test_project_date_validation(client: AsyncClient) -> None:
    email = unique_email("project-validate")
    created = await register(client, email=email)
    assert created.status_code == 201
    headers = await auth_headers(client)

    response = await client.post(
        "/api/v1/projects",
        json={
            "name": "Bad dates",
            "start_date": (date.today() + timedelta(days=10)).isoformat(),
            "due_date": date.today().isoformat(),
        },
        headers=headers,
    )
    assert response.status_code == 422


async def test_habit_crud_logs_and_streak(client: AsyncClient) -> None:
    email = unique_email("habit")
    created = await register(client, email=email)
    assert created.status_code == 201
    headers = await auth_headers(client)

    response = await client.post(
        "/api/v1/habits",
        json={
            "name": "Morning meditation",
            "schedule": "daily",
            "target_per_week": None,
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    habit = response.json()
    habit_id = habit["id"]
    assert habit["streak"] == 0
    assert habit["completions_last_30_days"] == 0

    today = date.today().isoformat()
    log = await client.post(
        f"/api/v1/habits/{habit_id}/logs",
        json={"log_date": today, "note": "Felt calm"},
        headers=headers,
    )
    assert log.status_code == 201, log.text
    assert log.json()["log_date"] == today

    fetched = await client.get(f"/api/v1/habits/{habit_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["streak"] == 1
    assert fetched.json()["completions_last_30_days"] == 1

    duplicate = await client.post(
        f"/api/v1/habits/{habit_id}/logs",
        json={"log_date": today},
        headers=headers,
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "habit_log_already_exists"

    logs = await client.get(f"/api/v1/habits/{habit_id}/logs", headers=headers)
    assert logs.status_code == 200
    assert len(logs.json()["logs"]) == 1

    undone = await client.delete(f"/api/v1/habits/{habit_id}/logs/{today}", headers=headers)
    assert undone.status_code == 204

    fetched = await client.get(f"/api/v1/habits/{habit_id}", headers=headers)
    assert fetched.json()["streak"] == 0

    async with make_client() as stranger:
        stranger_created = await register(stranger)
        assert stranger_created.status_code == 201
        stranger_headers = await auth_headers(stranger)

        cross = await stranger.delete(
            f"/api/v1/habits/{habit_id}/logs/{today}", headers=stranger_headers
        )
        assert cross.status_code == 404


async def test_habit_archive_and_list(client: AsyncClient) -> None:
    email = unique_email("habit-archive")
    created = await register(client, email=email)
    assert created.status_code == 201
    headers = await auth_headers(client)

    await client.post(
        "/api/v1/habits",
        json={"name": "Active habit", "schedule": "daily"},
        headers=headers,
    )
    archived = await client.post(
        "/api/v1/habits",
        json={"name": "Archived habit", "schedule": "weekly"},
        headers=headers,
    )
    assert archived.status_code == 201
    archived_id = archived.json()["id"]

    archive_resp = await client.post(f"/api/v1/habits/{archived_id}/archive", headers=headers)
    assert archive_resp.status_code == 204

    listed = await client.get("/api/v1/habits", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()["habits"]) == 1

    all_habits = await client.get("/api/v1/habits?include_archived=true", headers=headers)
    assert all_habits.status_code == 200
    assert len(all_habits.json()["habits"]) == 2

    unarchive = await client.post(f"/api/v1/habits/{archived_id}/unarchive", headers=headers)
    assert unarchive.status_code == 204


async def test_calendar_event_crud_and_range(client: AsyncClient) -> None:
    email = unique_email("calendar")
    created = await register(client, email=email)
    assert created.status_code == 201
    headers = await auth_headers(client)

    now = datetime.now(ZoneInfo("UTC"))
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start = now.replace(hour=9, minute=0, second=0, microsecond=0)
    end = now.replace(hour=10, minute=0, second=0, microsecond=0)

    response = await client.post(
        "/api/v1/calendar",
        json={
            "title": "Team standup",
            "description": "Daily sync",
            "starts_at": start.isoformat(),
            "ends_at": end.isoformat(),
            "all_day": False,
            "location": "Conference room A",
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    event = response.json()
    event_id = event["id"]
    assert event["title"] == "Team standup"
    assert event["all_day"] is False

    listed = await client.get(
        f"/api/v1/calendar?starts_after={start_of_day.isoformat().replace('+', '%2B')}"
        f"&ends_before={(now + timedelta(days=1)).isoformat().replace('+', '%2B')}",
        headers=headers,
    )
    assert listed.status_code == 200
    assert len(listed.json()["events"]) == 1

    updated = await client.patch(
        f"/api/v1/calendar/{event_id}",
        json={"title": "Team standup (updated)"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Team standup (updated)"

    deleted = await client.delete(f"/api/v1/calendar/{event_id}", headers=headers)
    assert deleted.status_code == 204

    async with make_client() as stranger:
        stranger_created = await register(stranger)
        assert stranger_created.status_code == 201
        stranger_headers = await auth_headers(stranger)

        cross = await stranger.get(f"/api/v1/calendar/{event_id}", headers=stranger_headers)
        assert cross.status_code == 404


async def test_calendar_event_time_validation(client: AsyncClient) -> None:
    email = unique_email("calendar-validate")
    created = await register(client, email=email)
    assert created.status_code == 201
    headers = await auth_headers(client)

    now = datetime.now(ZoneInfo("UTC"))
    response = await client.post(
        "/api/v1/calendar",
        json={
            "title": "Bad timing",
            "starts_at": (now + timedelta(hours=2)).isoformat(),
            "ends_at": now.isoformat(),
        },
        headers=headers,
    )
    assert response.status_code == 422


async def test_routine_crud_and_steps(client: AsyncClient) -> None:
    email = unique_email("routine")
    created = await register(client, email=email)
    assert created.status_code == 201
    headers = await auth_headers(client)

    response = await client.post(
        "/api/v1/routines",
        json={
            "name": "Morning routine",
            "description": "Start the day right",
            "time_of_day": "07:00",
            "is_active": True,
            "steps": [
                {"title": "Drink water", "duration_minutes": 5, "sort_order": 1},
                {"title": "Exercise", "duration_minutes": 30, "sort_order": 2},
            ],
        },
        headers=headers,
    )
    assert response.status_code == 201, response.text
    routine = response.json()
    routine_id = routine["id"]
    assert routine["step_count"] == 2
    assert len(routine["steps"]) == 2

    listed = await client.get("/api/v1/routines", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()["routines"]) == 1

    fetched = await client.get(f"/api/v1/routines/{routine_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "Morning routine"

    updated = await client.patch(
        f"/api/v1/routines/{routine_id}",
        json={"name": "Morning routine (updated)", "time_of_day": "07:30"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Morning routine (updated)"
    assert updated.json()["time_of_day"] == "07:30"

    new_step = await client.post(
        f"/api/v1/routines/{routine_id}/steps",
        json={"title": "Meditate", "duration_minutes": 10, "sort_order": 3},
        headers=headers,
    )
    assert new_step.status_code == 201

    step_id = new_step.json()["id"]
    step_updated = await client.patch(
        f"/api/v1/routines/steps/{step_id}",
        json={"duration_minutes": 15},
        headers=headers,
    )
    assert step_updated.status_code == 200
    assert step_updated.json()["duration_minutes"] == 15

    step_deleted = await client.delete(f"/api/v1/routines/steps/{step_id}", headers=headers)
    assert step_deleted.status_code == 204

    routine_deleted = await client.delete(f"/api/v1/routines/{routine_id}", headers=headers)
    assert routine_deleted.status_code == 204

    async with make_client() as stranger:
        stranger_created = await register(stranger)
        assert stranger_created.status_code == 201
        stranger_headers = await auth_headers(stranger)

        cross = await stranger.get(f"/api/v1/routines/{routine_id}", headers=stranger_headers)
        assert cross.status_code == 404


async def test_inactive_user_cannot_access_productivity(client: AsyncClient) -> None:
    email = unique_email("inactive")
    created = await register(client, email=email)
    assert created.status_code == 201
    headers = await auth_headers(client)

    async with SessionFactory() as db:
        await db.execute(update(User).where(User.email == email).values(is_active=False))
        await db.commit()

    endpoints = [
        ("GET", "/api/v1/tasks"),
        ("POST", "/api/v1/tasks"),
        ("GET", "/api/v1/goals"),
        ("POST", "/api/v1/goals"),
        ("GET", "/api/v1/projects"),
        ("POST", "/api/v1/projects"),
        ("GET", "/api/v1/habits"),
        ("POST", "/api/v1/habits"),
        ("GET", "/api/v1/calendar"),
        ("POST", "/api/v1/calendar"),
        ("GET", "/api/v1/routines"),
        ("POST", "/api/v1/routines"),
    ]
    for method, path in endpoints:
        if method == "GET":
            response = await client.get(path, headers=headers)
        else:
            response = await client.post(path, json={}, headers=headers)
        assert response.status_code in (401, 403), (
            f"{method} {path} returned {response.status_code}"
        )


# --- Deterministic engine unit tests ---


def _make_task(
    task_id: uuid.UUID,
    title: str,
    status: str = "todo",
    priority: str = "medium",
    due_at: datetime | None = None,
    planned_for: date | None = None,
    estimated_minutes: int | None = None,
    deleted_at: datetime | None = None,
) -> object:
    from app.db.models.task import Task

    return Task(
        id=task_id,
        user_id=uuid.uuid4(),
        title=title,
        status=status,
        priority=priority,
        due_at=due_at,
        planned_for=planned_for,
        estimated_minutes=estimated_minutes,
        deleted_at=deleted_at,
    )


async def test_task_prioritization_overdue_first() -> None:
    now = datetime(2026, 11, 7, 12, 0, tzinfo=UTC)
    tasks = [
        _make_task(uuid.uuid4(), "Overdue task", due_at=datetime(2026, 11, 1, tzinfo=UTC)),
        _make_task(uuid.uuid4(), "Due today", due_at=datetime(2026, 11, 7, tzinfo=UTC)),
        _make_task(uuid.uuid4(), "Due next week", due_at=datetime(2026, 11, 14, tzinfo=UTC)),
        _make_task(uuid.uuid4(), "No due date"),
    ]
    result = await asyncio_to_thread(prioritize_tasks, tasks, now=now)
    assert result.prioritized[0].title == "Overdue task"
    assert result.prioritized[0].score > result.prioritized[1].score
    assert "Overdue" in result.prioritized[0].reasons


async def test_task_prioritization_empty() -> None:
    result = await asyncio_to_thread(prioritize_tasks, [], now=datetime(2026, 11, 7, tzinfo=UTC))
    assert result.prioritized == []


def test_daily_plan_overload() -> None:
    now = datetime(2026, 11, 7, 12, 0, tzinfo=UTC)
    tasks = [
        _make_task(
            uuid.uuid4(),
            "Big task",
            due_at=datetime(2026, 11, 7, 9, tzinfo=UTC),
            estimated_minutes=500,
        ),
        _make_task(
            uuid.uuid4(),
            "Small task",
            due_at=datetime(2026, 11, 7, 10, tzinfo=UTC),
            estimated_minutes=30,
        ),
    ]
    plan = daily_plan(tasks, now=now)
    assert plan.overload is True
    assert plan.estimated_remaining_minutes == 530


def test_goal_progress_with_milestones() -> None:
    from app.db.models.goal import Goal
    from app.db.models.milestone import Milestone

    now = datetime(2026, 11, 7, tzinfo=UTC)
    goal = Goal(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        title="Test goal",
        status="active",
        target_date=date(2026, 12, 1),
    )
    milestones = [
        Milestone(id=uuid.uuid4(), goal_id=goal.id, title="M1", status="completed"),
        Milestone(id=uuid.uuid4(), goal_id=goal.id, title="M2", status="pending"),
    ]
    results = goal_progress([goal], milestones, [], now=now)
    assert results[0].progress == 50
    assert results[0].milestone_count == 2
    assert results[0].completed_milestone_count == 1


def test_habit_consistency_daily_streak() -> None:
    from app.db.models.habit import Habit, HabitLog

    now = datetime(2026, 11, 7, tzinfo=UTC)
    today = date(2026, 11, 7)
    habit = Habit(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        name="Daily habit",
        schedule="daily",
    )
    logs = [
        HabitLog(
            id=uuid.uuid4(),
            habit_id=habit.id,
            user_id=habit.user_id,
            log_date=today,
        ),
        HabitLog(
            id=uuid.uuid4(),
            habit_id=habit.id,
            user_id=habit.user_id,
            log_date=today - timedelta(days=1),
        ),
        HabitLog(
            id=uuid.uuid4(),
            habit_id=habit.id,
            user_id=habit.user_id,
            log_date=today - timedelta(days=2),
        ),
    ]
    results = habit_consistency([habit], logs, now=now)
    assert results[0].streak == 3
    assert results[0].completions_7d == 3


def test_detect_patterns_overdue_tasks() -> None:
    now = datetime(2026, 11, 7, tzinfo=UTC)
    tasks = [
        _make_task(uuid.uuid4(), "Overdue 1", due_at=datetime(2026, 11, 1, tzinfo=UTC)),
        _make_task(uuid.uuid4(), "Overdue 2", due_at=datetime(2026, 11, 2, tzinfo=UTC)),
        _make_task(uuid.uuid4(), "Overdue 3", due_at=datetime(2026, 11, 3, tzinfo=UTC)),
        _make_task(uuid.uuid4(), "Overdue 4", due_at=datetime(2026, 11, 4, tzinfo=UTC)),
        _make_task(uuid.uuid4(), "Overdue 5", due_at=datetime(2026, 11, 5, tzinfo=UTC)),
    ]
    patterns = detect_patterns([], [], tasks, [], now=now)
    deferral = [p for p in patterns if p.kind == "chronic_deferral"]
    assert len(deferral) == 1
    assert deferral[0].confidence == "high"


async def asyncio_to_thread(func, *args, **kwargs):
    import asyncio

    return await asyncio.to_thread(func, *args, **kwargs)


