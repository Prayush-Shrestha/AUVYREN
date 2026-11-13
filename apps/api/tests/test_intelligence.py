"""Intelligence engine tests: deterministic rules and provider API contracts."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

import pytest
from app.intelligence.deterministic import (
    Weights,
    daily_plan,
    deadline_awareness,
    detect_patterns,
    goal_progress,
    habit_consistency,
    prioritize_tasks,
    weekly_review_draft,
)
from app.main import app
from httpx import ASGITransport, AsyncClient

ORIGIN = "http://localhost:3000"
EMAIL_DOMAIN = "phase7.auvyren.app"
PASSWORD = "correct horse battery staple"
INTELLIGENCE = "/api/v1/intelligence"


def ns(**kwargs: object) -> SimpleNamespace:
    return SimpleNamespace(**kwargs)


def task(**overrides: object) -> SimpleNamespace:
    now = datetime.now(UTC)
    defaults = {
        "id": uuid.uuid4(),
        "title": "A task",
        "status": "todo",
        "deleted_at": None,
        "due_at": None,
        "priority": "medium",
        "estimated_minutes": 30,
        "project_id": None,
        "updated_at": now,
        "planned_for": None,
        "completed_at": None,
    }
    defaults.update(overrides)
    return ns(**defaults)


def goal(**overrides: object) -> SimpleNamespace:
    defaults = {
        "id": uuid.uuid4(),
        "title": "A goal",
        "status": "active",
        "deleted_at": None,
        "target_date": None,
        "manual_progress": None,
    }
    defaults.update(overrides)
    return ns(**defaults)


def milestone(**overrides: object) -> SimpleNamespace:
    now = datetime.now(UTC)
    defaults = {
        "id": uuid.uuid4(),
        "goal_id": uuid.uuid4(),
        "title": "A milestone",
        "status": "pending",
        "target_date": None,
        "completed_at": None,
        "updated_at": now,
        "created_at": now,
    }
    defaults.update(overrides)
    return ns(**defaults)


def habit(**overrides: object) -> SimpleNamespace:
    defaults = {
        "id": uuid.uuid4(),
        "name": "A habit",
        "schedule": "daily",
        "target_per_week": 3,
        "is_archived": False,
    }
    defaults.update(overrides)
    return ns(**defaults)


def log(habit_id: uuid.UUID, log_date: date) -> SimpleNamespace:
    return ns(habit_id=habit_id, log_date=log_date)


def test_weights_must_sum_to_one_hundred() -> None:
    with pytest.raises(ValueError):
        Weights(urgency=50)
    assert Weights().urgency == 30.0


def test_prioritize_orders_overdue_urgent_work_first() -> None:
    now = datetime(2026, 11, 8, 12, tzinfo=UTC)
    overdue = task(
        title="Overdue urgent",
        due_at=now - timedelta(days=2),
        priority="urgent",
    )
    soon = task(
        title="Due in three days",
        due_at=now + timedelta(days=2),
        priority="high",
    )
    later = task(title="No deadline", priority="low")

    result = prioritize_tasks([later, soon, overdue], now=now)

    assert [item.title for item in result.prioritized] == [
        "Overdue urgent",
        "Due in three days",
        "No deadline",
    ]
    assert "Overdue" in result.prioritized[0].reasons
    assert all(0 <= item.score <= 100 for item in result.prioritized)


def test_daily_plan_detects_overload_and_caps_priorities() -> None:
    now = datetime(2026, 11, 8, 9, tzinfo=UTC)
    tasks = [
        task(
            title=f"Task {index}",
            due_at=now + timedelta(hours=index),
            estimated_minutes=120,
        )
        for index in range(8)
    ]

    plan = daily_plan(tasks, now=now, available_minutes=300)

    assert plan.overload is True
    assert plan.estimated_remaining_minutes == 960
    assert len(plan.priorities) <= 5
    assert plan.focus_block_minutes == 75
    assert plan.slack_minutes == 225


def test_deadline_awareness_sorts_and_classifies() -> None:
    now = datetime(2026, 11, 8, 9, tzinfo=UTC)
    tasks = [task(title="Overdue", due_at=now - timedelta(days=2))]
    goals = [
        goal(
            title="Neglected",
            target_date=(now - timedelta(days=1)).date(),
        )
    ]
    milestones = [
        milestone(title="Soon", target_date=(now + timedelta(days=2)).date())
    ]

    items = deadline_awareness(tasks, goals, milestones, now=now)

    assert [item.kind for item in items] == ["task", "goal", "milestone"]
    assert items[0].classification == "overdue"
    assert items[1].classification == "overdue"
    assert items[2].classification == "due_1_3_days"


def test_goal_progress_uses_milestone_counts_and_manual_progress() -> None:
    now = datetime(2026, 11, 8, 9, tzinfo=UTC)
    counted = goal(title="Counted", target_date=(now + timedelta(days=10)).date())
    manual = goal(title="Manual", manual_progress=42)
    milestones = [
        milestone(goal_id=counted.id, status="completed"),
        milestone(goal_id=counted.id, status="pending"),
    ]

    progress = goal_progress([counted, manual], milestones, [], now=now)

    by_title = {item.title: item for item in progress}
    assert by_title["Counted"].progress == 50
    assert by_title["Counted"].is_neglected is False
    assert by_title["Manual"].progress == 42


def test_habit_consistency_streaks_and_missed_days() -> None:
    now = datetime(2026, 11, 8, 9, tzinfo=UTC)
    daily = habit(name="Daily")
    logs = [
        log(daily.id, now.date()),
        log(daily.id, (now - timedelta(days=1)).date()),
    ]

    result = habit_consistency([daily], logs, now=now)

    assert result[0].streak == 2
    assert result[0].completions_7d == 2
    assert len(result[0].missed_dates_7d) == 5
    assert result[0].is_inconsistent is False


def test_patterns_require_minimum_samples() -> None:
    now = datetime(2026, 11, 8, 9, tzinfo=UTC)
    overdue = [
        task(due_at=now - timedelta(days=1)),
        task(due_at=now - timedelta(days=2)),
        task(due_at=now - timedelta(days=3)),
    ]

    patterns = detect_patterns([], [], overdue, [], now=now)

    assert [item.kind for item in patterns] == ["chronic_deferral"]
    assert patterns[0].confidence == "medium"


def test_weekly_review_counts_completed_and_missed() -> None:
    now = datetime(2026, 11, 8, 9, tzinfo=UTC)
    completed = task(
        title="Done",
        status="done",
        completed_at=now - timedelta(days=1),
    )
    missed = task(title="Missed", due_at=now - timedelta(days=1))

    draft = weekly_review_draft([completed, missed], [], [], [], now=now)

    assert draft.completed_count == 1
    assert draft.missed_count == 1
    assert draft.priorities_next_week == ["Missed"]
    assert draft.week_start == date(2026, 11, 2)


def make_client() -> AsyncClient:
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
        headers={"Origin": ORIGIN, "Referer": f"{ORIGIN}/"},
    )


async def get_csrf(client: AsyncClient) -> str:
    response = await client.get("/api/v1/auth/csrf")
    assert response.status_code == 200, response.text
    return response.json()["csrf_token"]


async def register(client: AsyncClient) -> None:
    token = await get_csrf(client)
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": f"intelligence-{uuid.uuid4().hex}@{EMAIL_DOMAIN}",
            "password": PASSWORD,
            "full_name": "Intelligence Test",
        },
        headers={"X-CSRF-Token": token},
    )
    assert response.status_code == 201, response.text


async def auth_headers(client: AsyncClient) -> dict[str, str]:
    return {"X-CSRF-Token": await get_csrf(client)}


async def test_intelligence_endpoints_use_authenticated_workspace(
    client: AsyncClient,
) -> None:
    await register(client)
    headers = await auth_headers(client)
    now = datetime.now(UTC)

    created = await client.post(
        "/api/v1/tasks",
        json={
            "title": "Ship the intelligence dashboard",
            "priority": "urgent",
            "due_at": now.isoformat(),
            "estimated_minutes": 90,
        },
        headers=headers,
    )
    assert created.status_code == 201, created.text

    prioritize = await client.get(f"{INTELLIGENCE}/prioritize")
    assert prioritize.status_code == 200, prioritize.text
    assert prioritize.json()["prioritized"][0]["title"] == "Ship the intelligence dashboard"

    plan = await client.get(f"{INTELLIGENCE}/daily-plan")
    assert plan.status_code == 200, plan.text
    assert plan.json()["daily_plan"]["overload"] is False

    briefing = await client.get(f"{INTELLIGENCE}/briefing")
    assert briefing.status_code == 200, briefing.text
    assert briefing.json()["deadlines"][0]["kind"] == "task"

    for endpoint in (
        "deadlines",
        "goals/progress",
        "habits/consistency",
        "patterns",
        "weekly-review",
        "providers",
    ):
        response = await client.get(f"{INTELLIGENCE}/{endpoint}")
        assert response.status_code == 200, f"{endpoint}: {response.text}"

    ask = await client.post(
        f"{INTELLIGENCE}/ask",
        json={"question": "What should I work on next?", "provider": "deterministic"},
        headers=headers,
    )
    assert ask.status_code == 200, ask.text
    assert ask.json()["provider"] == "deterministic"
    assert "Deterministic summary" in ask.json()["answer"]


async def test_ask_requires_provider_consent(client: AsyncClient) -> None:
    await register(client)
    headers = await auth_headers(client)

    without_consent = await client.post(
        f"{INTELLIGENCE}/ask",
        json={"question": "Use my local model", "provider": "ollama"},
        headers=headers,
    )
    assert without_consent.status_code == 400
    assert without_consent.json()["code"] == "invalid_provider"
    assert "Consent" in without_consent.json()["detail"]

    unknown = await client.post(
        f"{INTELLIGENCE}/ask",
        json={"question": "Hello", "provider": "not-a-provider"},
        headers=headers,
    )
    assert unknown.status_code == 400
    assert unknown.json()["code"] == "invalid_provider"


async def test_configure_provider_rejects_unsupported_provider(
    client: AsyncClient,
) -> None:
    await register(client)
    headers = await auth_headers(client)

    response = await client.post(
        f"{INTELLIGENCE}/providers/configure",
        json={
            "provider": "cloud",
            "base_url": "https://api.example.com",
            "model": "example",
        },
        headers=headers,
    )
    assert response.status_code == 400
    assert response.json()["code"] == "invalid_provider"
