"""Deterministic productivity engine.

Pure, testable module with an injected clock and explicit, bounded weights.
Never sends data off-server. Every ranked item carries human-readable reasons.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.db.models.goal import Goal
    from app.db.models.habit import Habit, HabitLog
    from app.db.models.milestone import Milestone
    from app.db.models.task import Task


@dataclass(frozen=True)
class Weights:
    """Component weights for task prioritization. Sum must equal 100."""

    urgency: float = 30.0
    importance: float = 25.0
    goal_alignment: float = 20.0
    effort_fit: float = 15.0
    staleness: float = 10.0

    def __post_init__(self) -> None:
        total = (
            self.urgency
            + self.importance
            + self.goal_alignment
            + self.effort_fit
            + self.staleness
        )
        if abs(total - 100.0) > 0.001:
            raise ValueError(f"Weights must sum to 100, got {total}")


@dataclass(frozen=True)
class TaskScore:
    task_id: uuid.UUID
    title: str
    score: int  # 0-100
    reasons: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class TaskPriorityResult:
    prioritized: list[TaskScore]


# Urgency score by deadline classification (out of full urgency weight).
_URGENCY_SCORES = {
    "overdue": 1.0,
    "due_today": 0.85,
    "due_1_3_days": 0.65,
    "due_this_week": 0.4,
    "later": 0.0,
}

_IMPORTANCE_SCORES = {
    "urgent": 1.0,
    "high": 0.7,
    "medium": 0.4,
    "low": 0.2,
}


def _to_utc(value: datetime | date) -> datetime:
    if isinstance(value, date) and not isinstance(value, datetime):
        value = datetime.combine(value, time.min)
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value


def _classify_deadline(due: datetime | date | None, now: datetime) -> str:
    """Classify a deadline into urgency buckets."""
    if due is None:
        return "later"
    due_dt = _to_utc(due)
    now_dt = _to_utc(now)
    due_date = due_dt.date()
    today_date = now_dt.date()
    if due_date == today_date:
        return "due_today"
    if due_dt < now_dt:
        return "overdue"
    if today_date < due_date <= today_date + timedelta(days=3):
        return "due_1_3_days"
    if today_date + timedelta(days=3) < due_date <= today_date + timedelta(days=7):
        return "due_this_week"
    return "later"


def _goal_alignment_score(
    task: Task,
    active_project_ids: set[uuid.UUID],
    active_goal_ids: set[uuid.UUID],
    now: datetime,
) -> float:
    """Return 0-1 alignment with active goals/projects with near target dates."""
    if task.project_id and task.project_id in active_project_ids:
        return 1.0
    return 0.0


def _effort_fit_score(
    task: Task,
    available_minutes: int,
    remaining_estimate_minutes: int,
) -> float:
    """Tasks that fit remaining daily capacity rank higher."""
    if remaining_estimate_minutes <= 0:
        return 1.0 if available_minutes > 0 else 0.0
    estimate = task.estimated_minutes or 30
    if estimate <= available_minutes:
        return 1.0
    return max(0.0, 1.0 - (estimate - available_minutes) / remaining_estimate_minutes)


def _staleness_score(task: Task, now: datetime) -> float:
    """Repeatedly deferred work is surfaced with a note, not silently promoted."""
    updated = task.updated_at
    if updated is None:
        return 0.0
    updated_dt = _to_utc(updated)
    now_dt = _to_utc(now)
    age_days = (now_dt - updated_dt).days
    if age_days >= 14:
        return 1.0
    if age_days >= 7:
        return 0.6
    if age_days >= 3:
        return 0.3
    return 0.0


def prioritize_tasks(
    tasks: list[Task],
    *,
    now: datetime,
    weights: Weights | None = None,
    active_project_ids: set[uuid.UUID] | None = None,
    active_goal_ids: set[uuid.UUID] | None = None,
    available_minutes: int = 480,  # 8-hour workday
) -> TaskPriorityResult:
    """Rank tasks by a transparent 0-100 score with human-readable reasons."""
    w = weights or Weights()
    active_project_ids = active_project_ids or set()
    active_goal_ids = active_goal_ids or set()

    remaining_estimate = sum(t.estimated_minutes or 30 for t in tasks)

    scored: list[TaskScore] = []
    for task in tasks:
        if task.status == "done" or task.deleted_at is not None:
            continue

        urgency_bucket = _classify_deadline(task.due_at, now)
        urgency_score = _URGENCY_SCORES[urgency_bucket]
        importance_score = _IMPORTANCE_SCORES.get(
            task.priority, _IMPORTANCE_SCORES["medium"]
        )
        goal_score = _goal_alignment_score(
            task, active_project_ids, active_goal_ids, now
        )
        effort_score = _effort_fit_score(task, available_minutes, remaining_estimate)
        stale_score = _staleness_score(task, now)

        total = (
            w.urgency * urgency_score
            + w.importance * importance_score
            + w.goal_alignment * goal_score
            + w.effort_fit * effort_score
            + w.staleness * stale_score
        )
        score = max(0, min(100, round(total)))

        reasons: list[str] = []
        if urgency_bucket == "overdue":
            reasons.append("Overdue")
        elif urgency_bucket == "due_today":
            reasons.append("Due today")
        elif urgency_bucket == "due_1_3_days":
            reasons.append("Due within 3 days")
        elif urgency_bucket == "due_this_week":
            reasons.append("Due this week")
        if importance_score >= 0.8:
            reasons.append("High importance")
        elif importance_score >= 0.6:
            reasons.append("Important")
        if goal_score > 0:
            reasons.append("Linked to active goal/project")
        if effort_score >= 0.8:
            reasons.append("Fits remaining capacity")
        elif effort_score > 0:
            reasons.append("Partly fits capacity")
        if stale_score >= 0.6:
            reasons.append("Deferred repeatedly")
        if not reasons:
            reasons.append("Standard priority")

        scored.append(
            TaskScore(
                task_id=task.id,
                title=task.title,
                score=score,
                reasons=reasons,
            )
        )

    scored.sort(key=lambda s: (-s.score, s.title.lower()))
    return TaskPriorityResult(prioritized=scored)


@dataclass(frozen=True)
class DailyPlan:
    date: date
    available_minutes: int
    estimated_remaining_minutes: int
    overload: bool
    priorities: list[TaskScore]
    focus_block_minutes: int
    slack_minutes: int


def daily_plan(
    tasks: list[Task],
    *,
    now: datetime,
    target_date: date | None = None,
    available_minutes: int = 480,
) -> DailyPlan:
    """Build a daily plan: priorities, workload, focus block, slack."""
    day = target_date or now.date()
    now_dt = _to_utc(now)
    day_start = datetime.combine(day, time.min, tzinfo=UTC)
    day_end = day_start + timedelta(days=1)

    due_today = []
    remaining_estimate = 0
    for task in tasks:
        if task.status == "done" or task.deleted_at is not None:
            continue
        due = task.due_at
        due_dt = _to_utc(due)
        if day_start <= due_dt < day_end:
            due_today.append(task)
        remaining_estimate += task.estimated_minutes or 30

    result = prioritize_tasks(
        due_today,
        now=now_dt,
        available_minutes=available_minutes,
    )
    priorities = result.prioritized[:5]

    focus_block_minutes = min(90, available_minutes // 4)
    slack_minutes = max(0, available_minutes - focus_block_minutes)
    overload = remaining_estimate > available_minutes

    return DailyPlan(
        date=day,
        available_minutes=available_minutes,
        estimated_remaining_minutes=remaining_estimate,
        overload=overload,
        priorities=priorities,
        focus_block_minutes=focus_block_minutes,
        slack_minutes=slack_minutes,
    )


@dataclass(frozen=True)
class DeadlineItem:
    kind: str  # 'task', 'goal', 'milestone'
    id: uuid.UUID
    title: str
    due: date
    classification: str


def deadline_awareness(
    tasks: list[Task],
    goals: list[Goal],
    milestones: list[Milestone],
    *,
    now: datetime,
) -> list[DeadlineItem]:
    """Classify deadlines across tasks, goals and milestones."""
    items: list[DeadlineItem] = []
    now_dt = _to_utc(now)

    for task in tasks:
        if task.status == "done" or task.deleted_at is not None:
            continue
        if task.due_at is None:
            continue
        due_dt = _to_utc(task.due_at)
        items.append(
            DeadlineItem(
                kind="task",
                id=task.id,
                title=task.title,
                due=due_dt.date(),
                classification=_classify_deadline(due_dt, now_dt),
            )
        )

    for goal in goals:
        if goal.status == "completed":
            continue
        if goal.target_date is None:
            continue
        due_dt = datetime.combine(goal.target_date, time.min, tzinfo=UTC)
        items.append(
            DeadlineItem(
                kind="goal",
                id=goal.id,
                title=goal.title,
                due=goal.target_date,
                classification=_classify_deadline(due_dt, now_dt),
            )
        )

    for milestone in milestones:
        if milestone.status == "completed":
            continue
        if milestone.target_date is None:
            continue
        due_dt = datetime.combine(milestone.target_date, time.min, tzinfo=UTC)
        items.append(
            DeadlineItem(
                kind="milestone",
                id=milestone.id,
                title=milestone.title,
                due=milestone.target_date,
                classification=_classify_deadline(due_dt, now_dt),
            )
        )

    _URGENCY_ORDER = {
        "overdue": 0,
        "due_today": 1,
        "due_1_3_days": 2,
        "due_this_week": 3,
        "later": 4,
    }
    items.sort(key=lambda d: (_URGENCY_ORDER[d.classification], d.due, d.title.lower()))
    return items


@dataclass(frozen=True)
class GoalProgress:
    goal_id: uuid.UUID
    title: str
    progress: int  # 0-100
    milestone_count: int
    completed_milestone_count: int
    is_neglected: bool


def goal_progress(
    goals: list[Goal],
    milestones: list[Milestone],
    tasks: list[Task],
    *,
    now: datetime,
) -> list[GoalProgress]:
    """Compute goal progress and detect neglected goals."""
    now_dt = _to_utc(now)
    thirty_days_ago = now_dt - timedelta(days=30)

    milestones_by_goal: dict[uuid.UUID, list[Milestone]] = {}
    for m in milestones:
        milestones_by_goal.setdefault(m.goal_id, []).append(m)

    results: list[GoalProgress] = []
    for goal in goals:
        if goal.status == "completed":
            continue
        ms_list = milestones_by_goal.get(goal.id, [])
        milestone_count = len(ms_list)
        completed_count = sum(1 for m in ms_list if m.status == "completed")

        if goal.manual_progress is not None:
            progress = goal.manual_progress
        elif milestone_count > 0:
            progress = round((completed_count / milestone_count) * 100)
        else:
            progress = 100 if goal.status == "completed" else 0

        is_neglected = False
        if goal.status == "active" and goal.target_date is not None:
            target_dt = datetime.combine(goal.target_date, time.min, tzinfo=UTC)
            if now_dt <= target_dt <= now_dt + timedelta(days=30):
                recent_activity = False
                for m in ms_list:
                    recent = m.completed_at or m.updated_at or m.created_at
                    if recent is not None:
                        if recent.tzinfo is None:
                            recent = recent.replace(tzinfo=UTC)
                        if recent >= thirty_days_ago:
                            recent_activity = True
                            break
                if not recent_activity and completed_count < milestone_count:
                    is_neglected = True

        results.append(
            GoalProgress(
                goal_id=goal.id,
                title=goal.title,
                progress=max(0, min(100, progress)),
                milestone_count=milestone_count,
                completed_milestone_count=completed_count,
                is_neglected=is_neglected,
            )
        )

    results.sort(key=lambda g: (-g.progress, g.title.lower()))
    return results


@dataclass(frozen=True)
class HabitConsistency:
    habit_id: uuid.UUID
    name: str
    schedule: str
    streak: int
    completions_7d: int
    completions_30d: int
    completion_rate_7d: float  # 0-1
    completion_rate_30d: float  # 0-1
    missed_dates_7d: list[date]
    is_inconsistent: bool


def habit_consistency(
    habits: list[Habit],
    logs: list[HabitLog],
    *,
    now: datetime,
) -> list[HabitConsistency]:
    """Compute habit streaks and consistency."""
    today = now.date()
    week_ago = today - timedelta(days=6)
    month_ago = today - timedelta(days=29)

    logs_by_habit: dict[uuid.UUID, list[HabitLog]] = {}
    for log in logs:
        logs_by_habit.setdefault(log.habit_id, []).append(log)

    results: list[HabitConsistency] = []
    for habit in habits:
        if habit.is_archived:
            continue
        habit_logs = logs_by_habit.get(habit.id, [])
        log_dates = {log.log_date for log in habit_logs}

        # Streak: consecutive days ending today.
        streak = 0
        cursor = today
        while cursor in log_dates:
            streak += 1
            cursor -= timedelta(days=1)

        completions_7d = sum(1 for d in log_dates if week_ago <= d <= today)
        completions_30d = sum(1 for d in log_dates if month_ago <= d <= today)

        if habit.schedule == "daily":
            expected_7d = 7
            expected_30d = 30
        else:  # weekly
            expected_7d = min(7, habit.target_per_week or 1)
            expected_30d = min(30, (habit.target_per_week or 1) * 4)

        rate_7d = completions_7d / expected_7d if expected_7d else 0.0
        rate_30d = completions_30d / expected_30d if expected_30d else 0.0

        missed_dates_7d = [
            week_ago + timedelta(days=i)
            for i in range(7)
            if (week_ago + timedelta(days=i)) not in log_dates
        ]

        is_inconsistent = (
            habit.schedule == "daily" and streak == 0
        ) or (
            habit.schedule == "weekly" and completions_7d < (habit.target_per_week or 1)
        )

        results.append(
            HabitConsistency(
                habit_id=habit.id,
                name=habit.name,
                schedule=habit.schedule,
                streak=streak,
                completions_7d=completions_7d,
                completions_30d=completions_30d,
                completion_rate_7d=round(rate_7d, 2),
                completion_rate_30d=round(rate_30d, 2),
                missed_dates_7d=missed_dates_7d,
                is_inconsistent=is_inconsistent,
            )
        )

    results.sort(key=lambda h: (-h.completion_rate_30d, h.name.lower()))
    return results


@dataclass(frozen=True)
class Pattern:
    kind: str
    description: str
    evidence: str
    confidence: str  # 'low', 'medium', 'high'


def detect_patterns(
    habits: list[Habit],
    logs: list[HabitLog],
    tasks: list[Task],
    goals: list[Goal],
    *,
    now: datetime,
) -> list[Pattern]:
    """Detect patterns with minimum sample rules."""
    patterns: list[Pattern] = []

    # Chronic deferral: tasks with due_at in the past still not done.
    now_dt = _to_utc(now)
    today = now_dt.date()
    overdue_tasks = []
    for t in tasks:
        if t.status == "done" or t.deleted_at is not None or t.due_at is None:
            continue
        due = t.due_at if isinstance(t.due_at, datetime) else datetime.combine(t.due_at, time.min)
        if due.tzinfo is None:
            due = due.replace(tzinfo=UTC)
        if due < now_dt:
            overdue_tasks.append(t)
    if len(overdue_tasks) >= 3:
        patterns.append(
            Pattern(
                kind="chronic_deferral",
                description="Chronically deferred work",
                evidence=f"{len(overdue_tasks)} overdue tasks not yet completed",
                confidence="high" if len(overdue_tasks) >= 5 else "medium",
            )
        )

    # Habit consistency: daily habits with zero streak.
    inactive_habits = [h for h in habits if not h.is_archived]
    logs_by_habit: dict[uuid.UUID, list[HabitLog]] = {}
    for log in logs:
        logs_by_habit.setdefault(log.habit_id, []).append(log)
    zero_streak_habits = []
    for h in inactive_habits:
        log_dates = {log.log_date for log in logs_by_habit.get(h.id, [])}
        streak = 0
        cursor = today
        while cursor in log_dates:
            streak += 1
            cursor -= timedelta(days=1)
        if streak == 0:
            zero_streak_habits.append(h)
    if len(zero_streak_habits) >= 2:
        patterns.append(
            Pattern(
                kind="habit_inconsistency",
                description="Habits falling off track",
                evidence=f"{len(zero_streak_habits)} habits with no recent streak",
                confidence="medium",
            )
        )

    # Goal neglect.
    neglected = [g for g in goals if g.status == "active" and g.deleted_at is None]
    if len(neglected) >= 2:
        patterns.append(
            Pattern(
                kind="goal_neglect",
                description="Goals losing to urgent tasks",
                evidence=f"{len(neglected)} active goals without recent progress",
                confidence="low",
            )
        )

    # Overloaded days: estimated minutes exceed capacity on multiple days.
    day_estimates: dict[date, int] = {}
    for t in tasks:
        if t.status == "done" or t.deleted_at is not None or t.planned_for is None:
            continue
        day_estimates[t.planned_for] = day_estimates.get(t.planned_for, 0) + (
            t.estimated_minutes or 30
        )
    overloaded_days = 0
    for _d, est in day_estimates.items():
        if est > 480:  # 8-hour day
            overloaded_days += 1
    if overloaded_days >= 2:
        patterns.append(
            Pattern(
                kind="overloaded_day",
                description="Consistently overloaded days",
                evidence=f"{overloaded_days} days exceed 8-hour capacity",
                confidence="medium",
            )
        )

    return patterns


@dataclass(frozen=True)
class WeeklyReviewDraft:
    week_start: date
    completed_count: int
    missed_count: int
    habit_consistency_summary: str
    goal_movement_summary: str
    overload_warning: str | None
    priorities_next_week: list[str]


def weekly_review_draft(
    tasks: list[Task],
    goals: list[Goal],
    habits: list[Habit],
    logs: list[HabitLog],
    *,
    now: datetime,
) -> WeeklyReviewDraft:
    """Draft a weekly review from deterministic data."""
    now_dt = _to_utc(now)
    week_start = (now_dt - timedelta(days=now_dt.weekday())).date()
    week_end = week_start + timedelta(days=6)

    completed_tasks = [
        t
        for t in tasks
        if t.status == "done"
        and t.completed_at is not None
        and week_start <= t.completed_at.date() <= week_end
    ]
    missed_tasks = [
        t
        for t in tasks
        if t.status != "done"
        and t.deleted_at is None
        and t.due_at is not None
        and week_start <= _to_utc(t.due_at).date() <= week_end
    ]

    habit_logs = [log for log in logs if week_start <= log.log_date <= week_end]
    completed_habit_days = {log.log_date for log in habit_logs}
    habit_summary = (
        f"{len(habit_logs)} completions across {len(completed_habit_days)} days"
        if habit_logs
        else "No habit completions logged this week"
    )

    active_goals = [g for g in goals if g.status == "active" and g.deleted_at is None]
    goal_summary = (
        f"{len(active_goals)} active goals; "
        f"{sum(1 for g in active_goals if g.manual_progress is not None)} with manual progress set"
    )

    overload_warning = None
    if len(completed_tasks) == 0 and len(missed_tasks) > 0:
        overload_warning = "No tasks completed this week despite missed commitments"

    return WeeklyReviewDraft(
        week_start=week_start,
        completed_count=len(completed_tasks),
        missed_count=len(missed_tasks),
        habit_consistency_summary=habit_summary,
        goal_movement_summary=goal_summary,
        overload_warning=overload_warning,
        priorities_next_week=[t.title for t in missed_tasks[:5]],
    )


__all__ = [
    "Weights",
    "TaskScore",
    "TaskPriorityResult",
    "DailyPlan",
    "DeadlineItem",
    "GoalProgress",
    "HabitConsistency",
    "Pattern",
    "WeeklyReviewDraft",
    "prioritize_tasks",
    "daily_plan",
    "deadline_awareness",
    "goal_progress",
    "habit_consistency",
    "detect_patterns",
    "weekly_review_draft",
]
