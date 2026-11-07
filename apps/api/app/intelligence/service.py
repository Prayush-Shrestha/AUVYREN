"""Intelligence service: provider orchestration, context minimization, provenance."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from app.intelligence.deterministic import (
    daily_plan,
    deadline_awareness,
    detect_patterns,
    goal_progress,
    habit_consistency,
    prioritize_tasks,
    weekly_review_draft,
)
from app.intelligence.providers import (
    AIRequest,
    AIResponse,
    CloudAIProvider,
    DeterministicProvider,
    OllamaProvider,
    new_provider_secret,
    secret_hash,
)
from app.intelligence.schemas import (
    AskRequest,
    AskResponse,
    BriefingResponse,
    DailyPlanResponse,
    DeadlineAwarenessResponse,
    GoalProgressResponse,
    HabitConsistencyResponse,
    PatternResponse,
    ProviderConfigureRequest,
    ProviderConfigureResponse,
    ProviderInfoResponse,
    ProviderSecretResponse,
    TaskPrioritizeResponse,
    WeeklyReviewDraftResponse,
)
from app.services.auth import CurrentAuth

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class IntelligenceService:
    """Orchestrates providers, minimizes context, tracks provenance."""

    def __init__(
        self,
        deterministic: DeterministicProvider,
        ollama: OllamaProvider | None,
        cloud: CloudAIProvider,
    ) -> None:
        self._providers: dict[str, object] = {
            deterministic.name: deterministic,
            cloud.name: cloud,
        }
        if ollama is not None:
            self._providers[ollama.name] = ollama
        self._ollama = ollama

    def _provider_for(
        self, name: str, auth: CurrentAuth | None = None
    ) -> object:
        provider = self._providers.get(name)
        if provider is None:
            raise KeyError(f"Unknown provider: {name}")
        return provider

    async def health_all(self) -> dict[str, object]:
        results: dict[str, object] = {}
        for name, provider in self._providers.items():
            results[name] = await provider.health()
        return results

    async def list_models_all(self) -> dict[str, list[str]]:
        results: dict[str, list[str]] = {}
        for name, provider in self._providers.items():
            results[name] = await provider.list_models()
        return results

    # Deterministic capabilities ------------------------------------------------

    async def prioritize_tasks(
        self, auth: CurrentAuth, db: AsyncSession
    ) -> TaskPrioritizeResponse:
        from sqlalchemy import select

        from app.db.models.task import Task

        result = await db.execute(
            select(Task).where(
                Task.user_id == auth.user.id,
                Task.deleted_at.is_(None),
            )
        )
        tasks = list(result.scalars().all())
        now = datetime.now(UTC)
        engine_result = prioritize_tasks(tasks, now=now)
        return TaskPrioritizeResponse(
            prioritized=[
                {
                    "task_id": s.task_id,
                    "title": s.title,
                    "score": s.score,
                    "reasons": s.reasons,
                }
                for s in engine_result.prioritized
            ]
        )

    async def daily_plan(self, auth: CurrentAuth, db: AsyncSession) -> DailyPlanResponse:
        from sqlalchemy import select

        from app.db.models.task import Task

        result = await db.execute(
            select(Task).where(
                Task.user_id == auth.user.id,
                Task.deleted_at.is_(None),
            )
        )
        tasks = list(result.scalars().all())
        now = datetime.now(UTC)
        plan = daily_plan(tasks, now=now)
        return DailyPlanResponse(
            date=plan.date,
            available_minutes=plan.available_minutes,
            estimated_remaining_minutes=plan.estimated_remaining_minutes,
            overload=plan.overload,
            priorities=[
                {
                    "task_id": s.task_id,
                    "title": s.title,
                    "score": s.score,
                    "reasons": s.reasons,
                }
                for s in plan.priorities
            ],
            focus_block_minutes=plan.focus_block_minutes,
            slack_minutes=plan.slack_minutes,
        )

    async def deadline_awareness(
        self, auth: CurrentAuth, db: AsyncSession
    ) -> DeadlineAwarenessResponse:
        from sqlalchemy import select

        from app.db.models.goal import Goal
        from app.db.models.milestone import Milestone
        from app.db.models.task import Task

        tasks = list(
            (await db.execute(
                select(Task).where(
                    Task.user_id == auth.user.id,
                    Task.deleted_at.is_(None),
                )
            )).scalars().all()
        )
        goals = list(
            (await db.execute(
                select(Goal).where(
                    Goal.user_id == auth.user.id,
                    Goal.deleted_at.is_(None),
                )
            )).scalars().all()
        )
        milestones = list(
            (await db.execute(
                select(Milestone).join(Goal).where(
                    Goal.user_id == auth.user.id,
                    Goal.deleted_at.is_(None),
                )
            )).scalars().all()
        )
        now = datetime.now(UTC)
        items = deadline_awareness(tasks, goals, milestones, now=now)
        return DeadlineAwarenessResponse(
            items=[
                {
                    "kind": i.kind,
                    "id": i.id,
                    "title": i.title,
                    "due": i.due,
                    "classification": i.classification,
                }
                for i in items
            ]
        )

    async def goal_progress(
        self, auth: CurrentAuth, db: AsyncSession
    ) -> list[GoalProgressResponse]:
        from sqlalchemy import select

        from app.db.models.goal import Goal
        from app.db.models.milestone import Milestone
        from app.db.models.task import Task

        goals = list(
            (await db.execute(
                select(Goal).where(
                    Goal.user_id == auth.user.id,
                    Goal.deleted_at.is_(None),
                )
            )).scalars().all()
        )
        milestones = list(
            (await db.execute(
                select(Milestone).join(Goal).where(
                    Goal.user_id == auth.user.id,
                    Goal.deleted_at.is_(None),
                )
            )).scalars().all()
        )
        tasks = list(
            (await db.execute(
                select(Task).where(
                    Task.user_id == auth.user.id,
                    Task.deleted_at.is_(None),
                )
            )).scalars().all()
        )
        now = datetime.now(UTC)
        progress = goal_progress(goals, milestones, tasks, now=now)
        return [
            GoalProgressResponse(
                goal_id=p.goal_id,
                title=p.title,
                progress=p.progress,
                milestone_count=p.milestone_count,
                completed_milestone_count=p.completed_milestone_count,
                is_neglected=p.is_neglected,
            )
            for p in progress
        ]

    async def habit_consistency(
        self, auth: CurrentAuth, db: AsyncSession
    ) -> list[HabitConsistencyResponse]:
        from sqlalchemy import select

        from app.db.models.habit import Habit, HabitLog
        from app.db.models.user import UserSettings

        habits = list(
            (await db.execute(
                select(Habit).where(
                    Habit.user_id == auth.user.id,
                    Habit.is_archived == False,  # noqa: E712
                )
            )).scalars().all()
        )
        logs = list(
            (await db.execute(
                select(HabitLog).where(HabitLog.user_id == auth.user.id)
            )).scalars().all()
        )
        await db.execute(
            select(UserSettings).where(UserSettings.user_id == auth.user.id)
        )
        now = datetime.now(UTC)
        consistency = habit_consistency(
            habits, logs, now=now
        )
        return [
            HabitConsistencyResponse(
                habit_id=h.habit_id,
                name=h.name,
                schedule=h.schedule,
                streak=h.streak,
                completions_7d=h.completions_7d,
                completions_30d=h.completions_30d,
                completion_rate_7d=h.completion_rate_7d,
                completion_rate_30d=h.completion_rate_30d,
                missed_dates_7d=h.missed_dates_7d,
                is_inconsistent=h.is_inconsistent,
            )
            for h in consistency
        ]

    async def patterns(self, auth: CurrentAuth, db: AsyncSession) -> list[PatternResponse]:
        from sqlalchemy import select

        from app.db.models.goal import Goal
        from app.db.models.habit import Habit, HabitLog
        from app.db.models.task import Task

        habits = list(
            (await db.execute(
                select(Habit).where(
                    Habit.user_id == auth.user.id,
                    Habit.is_archived == False,  # noqa: E712
                )
            )).scalars().all()
        )
        logs = list(
            (await db.execute(
                select(HabitLog).where(HabitLog.user_id == auth.user.id)
            )).scalars().all()
        )
        tasks = list(
            (await db.execute(
                select(Task).where(
                    Task.user_id == auth.user.id,
                    Task.deleted_at.is_(None),
                )
            )).scalars().all()
        )
        goals = list(
            (await db.execute(
                select(Goal).where(
                    Goal.user_id == auth.user.id,
                    Goal.deleted_at.is_(None),
                )
            )).scalars().all()
        )
        now = datetime.now(UTC)
        detected = detect_patterns(
            habits, logs, tasks, goals, now=now
        )
        return [
            PatternResponse(
                kind=p.kind,
                description=p.description,
                evidence=p.evidence,
                confidence=p.confidence,
            )
            for p in detected
        ]

    async def briefing(self, auth: CurrentAuth, db: AsyncSession) -> BriefingResponse:
        """Daily briefing: plan, deadlines, goals, habits, patterns."""
        plan = await self.daily_plan(auth, db)
        deadlines = await self.deadline_awareness(auth, db)
        goals = await self.goal_progress(auth, db)
        habits = await self.habit_consistency(auth, db)
        patterns = await self.patterns(auth, db)
        now = datetime.now(UTC)
        return BriefingResponse(
            date=now.date(),
            daily_plan=plan,
            deadlines=deadlines.items,
            goal_progress=goals,
            habit_consistency=habits,
            patterns=patterns,
        )

    async def weekly_review(self, auth: CurrentAuth, db: AsyncSession) -> WeeklyReviewDraftResponse:
        from sqlalchemy import select

        from app.db.models.goal import Goal
        from app.db.models.habit import Habit, HabitLog
        from app.db.models.task import Task

        tasks = list(
            (await db.execute(
                select(Task).where(
                    Task.user_id == auth.user.id,
                    Task.deleted_at.is_(None),
                )
            )).scalars().all()
        )
        goals = list(
            (await db.execute(
                select(Goal).where(
                    Goal.user_id == auth.user.id,
                    Goal.deleted_at.is_(None),
                )
            )).scalars().all()
        )
        habits = list(
            (await db.execute(
                select(Habit).where(
                    Habit.user_id == auth.user.id,
                    Habit.is_archived == False,  # noqa: E712
                )
            )).scalars().all()
        )
        logs = list(
            (await db.execute(
                select(HabitLog).where(HabitLog.user_id == auth.user.id)
            )).scalars().all()
        )
        now = datetime.now(UTC)
        draft = weekly_review_draft(tasks, goals, habits, logs, now=now)
        return WeeklyReviewDraftResponse(
            week_start=draft.week_start,
            completed_count=draft.completed_count,
            missed_count=draft.missed_count,
            habit_consistency_summary=draft.habit_consistency_summary,
            goal_movement_summary=draft.goal_movement_summary,
            overload_warning=draft.overload_warning,
            priorities_next_week=draft.priorities_next_week,
        )

    # Provider generation -------------------------------------------------------

    async def ask(
        self,
        auth: CurrentAuth,
        db: AsyncSession,
        request: AskRequest,
    ) -> AskResponse:
        """Workspace Q&A via the selected provider, with deterministic fallback."""
        provider = self._provider_for(request.provider, auth)
        context = await self._minimized_context(auth, db)

        ai_request = AIRequest(
            task=request.question,
            system_instructions=(
                "You are Auvyren's intelligence assistant. Answer using only the "
                "provided workspace context. Do not invent facts. If the answer is "
                "not in the context, say so. Keep replies concise and cite the "
                "records you used."
            ),
            context=context,
            max_output_tokens=500,
            temperature=0.2,
        )

        try:
            ai_response: AIResponse = await provider.generate(ai_request)
        except NotImplementedError:
            # Cloud AI is Phase 6; fall back to deterministic.
            ai_response = await self._providers["deterministic"].generate(ai_request)

        return AskResponse(
            answer=ai_response.text,
            provider=ai_response.provider,
            model=ai_response.model,
            usage=ai_response.usage,
            generated_at=ai_response.generated_at,
        )

    async def _minimized_context(self, auth: CurrentAuth, db: AsyncSession) -> dict:
        """Build a minimized, user-scoped context snapshot."""
        from sqlalchemy import select

        from app.db.models.goal import Goal
        from app.db.models.habit import Habit
        from app.db.models.milestone import Milestone
        from app.db.models.task import Task

        tasks = list(
            (await db.execute(
                select(Task).where(
                    Task.user_id == auth.user.id,
                    Task.deleted_at.is_(None),
                    Task.status != "done",
                ).limit(50)
            )).scalars().all()
        )
        goals = list(
            (await db.execute(
                select(Goal).where(
                    Goal.user_id == auth.user.id,
                    Goal.deleted_at.is_(None),
                ).limit(20)
            )).scalars().all()
        )
        habits = list(
            (await db.execute(
                select(Habit).where(
                    Habit.user_id == auth.user.id,
                    Habit.is_archived == False,  # noqa: E712
                ).limit(30)
            )).scalars().all()
        )
        milestones = list(
            (await db.execute(
                select(Milestone).join(Goal).where(
                    Goal.user_id == auth.user.id,
                    Goal.deleted_at.is_(None),
                    Milestone.deleted_at.is_(None),
                ).limit(50)
            )).scalars().all()
        )

        return {
            "user_id": str(auth.user.id),
            "tasks": [
                {
                    "id": str(t.id),
                    "title": t.title,
                    "status": t.status,
                    "priority": t.priority,
                    "due_at": t.due_at.isoformat() if t.due_at else None,
                }
                for t in tasks
            ],
            "goals": [
                {
                    "id": str(g.id),
                    "title": g.title,
                    "status": g.status,
                    "target_date": g.target_date.isoformat() if g.target_date else None,
                }
                for g in goals
            ],
            "habits": [
                {
                    "id": str(h.id),
                    "name": h.name,
                    "schedule": h.schedule,
                }
                for h in habits
            ],
            "milestones": [
                {
                    "id": str(m.id),
                    "title": m.title,
                    "goal_id": str(m.goal_id),
                    "status": m.status,
                }
                for m in milestones
            ],
        }

    # Provider configuration ----------------------------------------------------

    async def configure_provider(
        self, auth: CurrentAuth, db: AsyncSession, request: ProviderConfigureRequest
    ) -> ProviderConfigureResponse:
        from sqlalchemy import select

        from app.db.models.ai import AIProviderConfig

        if request.provider != "ollama":
            raise ValueError("Only ollama provider is configurable in Phase 4")

        secret = new_provider_secret()
        secret_hash_value = secret_hash(secret)

        result = await db.execute(
            select(AIProviderConfig).where(
                AIProviderConfig.user_id == auth.user.id,
                AIProviderConfig.provider == request.provider,
            )
        )
        existing = result.scalar_one_or_none()
        if existing is None:
            config = AIProviderConfig(
                user_id=auth.user.id,
                provider=request.provider,
                base_url=request.base_url,
                model=request.model,
                encrypted_secret=secret,
                secret_hash=secret_hash_value,
                is_default=True,
                enabled=True,
            )
            db.add(config)
        else:
            existing.base_url = request.base_url
            existing.model = request.model
            existing.encrypted_secret = secret
            existing.secret_hash = secret_hash_value
            existing.enabled = True
            existing.is_default = True

        await db.commit()

        # Verify connectivity.
        provider = OllamaProvider(
            base_url=request.base_url,
            model=request.model,
            timeout_seconds=10,
        )
        health = await provider.health()

        return ProviderConfigureResponse(
            provider=request.provider,
            base_url=request.base_url,
            model=request.model,
            healthy=health["healthy"],
            detail=health["detail"],
            secret_hash=secret_hash_value,
        )

    async def provider_secret(
        self, auth: CurrentAuth, db: AsyncSession
    ) -> ProviderSecretResponse:
        from sqlalchemy import select

        from app.db.models.ai import AIProviderConfig

        result = await db.execute(
            select(AIProviderConfig.secret_hash).where(
                AIProviderConfig.user_id == auth.user.id,
                AIProviderConfig.provider == "ollama",
            )
        )
        row = result.scalar_one_or_none()
        return ProviderSecretResponse(secret_hash=row)

    async def list_providers(
        self, auth: CurrentAuth, db: AsyncSession
    ) -> list[ProviderInfoResponse]:
        from sqlalchemy import select

        from app.db.models.ai import AIProviderConfig

        result = await db.execute(
            select(AIProviderConfig).where(
                AIProviderConfig.user_id == auth.user.id,
            )
        )
        configs = result.scalars().all()

        infos: list[ProviderInfoResponse] = []
        for cfg in configs:
            if cfg.provider == "ollama":
                provider = OllamaProvider(
                    base_url=cfg.base_url,
                    model=cfg.model or "",
                    timeout_seconds=10,
                )
                health = await provider.health()
                infos.append(
                    ProviderInfoResponse(
                        name=cfg.provider,
                        healthy=health["healthy"],
                        detail=health["detail"],
                        models=health.get("models", []),
                    )
                )
            elif cfg.provider == "deterministic":
                infos.append(
                    ProviderInfoResponse(
                        name="deterministic",
                        healthy=True,
                        detail="Always available",
                        models=["deterministic"],
                    )
                )
            elif cfg.provider == "cloud":
                infos.append(
                    ProviderInfoResponse(
                        name="cloud",
                        healthy=False,
                        detail="Cloud AI not available in Phase 4",
                        models=[],
                    )
                )
        return infos
