"""Intelligence engine API routes: deterministic productivity + provider access.

All routes require an authenticated session. Mutating routes additionally require
CSRF validation. Cloud AI is not available in Phase 4; deterministic fallback is
always used when no local provider is configured.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_auth, require_csrf
from app.api.errors import AppError
from app.db.session import get_db_session
from app.intelligence.providers import (
    CloudAIProvider,
    DeterministicProvider,
    OllamaProvider,
)
from app.intelligence.schemas import (
    AskRequest,
    AskResponse,
    BriefingResponse,
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
from app.intelligence.service import IntelligenceService
from app.services.auth import CurrentAuth

router = APIRouter(
    prefix="/intelligence",
    tags=["Intelligence"],
    dependencies=[Depends(require_csrf)],
)


async def _build_service(
    *,
    db: AsyncSession,
    auth: CurrentAuth | None,
) -> IntelligenceService:
    """Build an IntelligenceService with provider configs from the DB."""
    from sqlalchemy import select

    from app.db.models.ai import AIProviderConfig

    deterministic = DeterministicProvider()
    cloud = CloudAIProvider()
    ollama: OllamaProvider | None = None

    result = await db.execute(
        select(AIProviderConfig).where(
            AIProviderConfig.user_id == auth.user.id,
            AIProviderConfig.provider == "ollama",
            AIProviderConfig.enabled.is_(True),
        )
    )
    cfg = result.scalar_one_or_none()
    if cfg is not None and cfg.base_url:
        ollama = OllamaProvider(
            base_url=cfg.base_url,
            model=cfg.model or "",
        )

    return IntelligenceService(
        deterministic=deterministic,
        ollama=ollama,
        cloud=cloud,
    )


@router.get(
    "/prioritize",
    response_model=TaskPrioritizeResponse,
    summary="Prioritize tasks deterministically",
)
async def prioritize(
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> TaskPrioritizeResponse:
    service = await _build_service(db=db, auth=auth)
    return await service.prioritize_tasks(auth, db)


@router.get(
    "/daily-plan",
    response_model=BriefingResponse,
    summary="Daily plan and workload",
)
async def daily_plan(
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> BriefingResponse:
    service = await _build_service(db=db, auth=auth)
    return await service.briefing(auth, db)


@router.get(
    "/deadlines",
    response_model=DeadlineAwarenessResponse,
    summary="Deadline awareness across tasks, goals, milestones",
)
async def deadlines(
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> DeadlineAwarenessResponse:
    service = await _build_service(db=db, auth=auth)
    return await service.deadline_awareness(auth, db)


@router.get(
    "/goals/progress",
    response_model=list[GoalProgressResponse],
    summary="Goal progress calculations",
)
async def goals_progress(
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> list[GoalProgressResponse]:
    service = await _build_service(db=db, auth=auth)
    return await service.goal_progress(auth, db)


@router.get(
    "/habits/consistency",
    response_model=list[HabitConsistencyResponse],
    summary="Habit consistency and streaks",
)
async def habits_consistency(
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> list[HabitConsistencyResponse]:
    service = await _build_service(db=db, auth=auth)
    return await service.habit_consistency(auth, db)


@router.get(
    "/patterns",
    response_model=list[PatternResponse],
    summary="Pattern detection (minimum sample rules)",
)
async def patterns(
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> list[PatternResponse]:
    service = await _build_service(db=db, auth=auth)
    return await service.patterns(auth, db)


@router.get(
    "/briefing",
    response_model=BriefingResponse,
    summary="Daily briefing: plan, deadlines, goals, habits, patterns",
)
async def briefing(
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> BriefingResponse:
    service = await _build_service(db=db, auth=auth)
    return await service.briefing(auth, db)


@router.get(
    "/weekly-review",
    response_model=WeeklyReviewDraftResponse,
    summary="Weekly review draft",
)
async def weekly_review(
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> WeeklyReviewDraftResponse:
    service = await _build_service(db=db, auth=auth)
    return await service.weekly_review(auth, db)


@router.post(
    "/ask",
    response_model=AskResponse,
    summary="Workspace Q&A via configured provider (deterministic fallback)",
)
async def ask(
    payload: AskRequest,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> AskResponse:
    service = await _build_service(db=db, auth=auth)
    try:
        return await service.ask(auth, db, payload)
    except ValueError as exc:
        raise AppError(
            400,
            "invalid_provider",
            title="Provider unavailable",
            detail=str(exc),
        ) from exc


@router.get(
    "/providers",
    response_model=list[ProviderInfoResponse],
    summary="List configured AI providers and their health",
)
async def list_providers(
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> list[ProviderInfoResponse]:
    service = await _build_service(db=db, auth=auth)
    return await service.list_providers(auth, db)


@router.post(
    "/providers/configure",
    response_model=ProviderConfigureResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Configure the Ollama provider (URL, model)",
)
async def configure_provider(
    payload: ProviderConfigureRequest,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> ProviderConfigureResponse:
    service = await _build_service(db=db, auth=auth)
    try:
        return await service.configure_provider(auth, db, payload)
    except ValueError as exc:
        raise AppError(
            400,
            "invalid_provider",
            title="Provider unavailable",
            detail=str(exc),
        ) from exc


@router.get(
    "/providers/secret",
    response_model=ProviderSecretResponse,
    summary="Get the stored provider secret hash (change detection only)",
)
async def provider_secret(
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> ProviderSecretResponse:
    service = await _build_service(db=db, auth=auth)
    return await service.provider_secret(auth, db)


@router.get(
    "/providers/{provider_name}/health",
    response_model=ProviderInfoResponse,
    summary="Check health of a configured provider",
)
async def provider_health(
    provider_name: str,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> ProviderInfoResponse:
    from sqlalchemy import select

    from app.db.models.ai import AIProviderConfig

    result = await db.execute(
        select(AIProviderConfig).where(
            AIProviderConfig.user_id == auth.user.id,
            AIProviderConfig.provider == provider_name,
            AIProviderConfig.enabled.is_(True),
        )
    )
    cfg = result.scalar_one_or_none()
    if cfg is None:
        raise AppError(
            404,
            "provider_not_configured",
            title="Provider not configured",
            detail=f"Provider '{provider_name}' is not configured.",
        )

    if provider_name == "ollama":
        provider = OllamaProvider(
            base_url=cfg.base_url or "",
            model=cfg.model or "",
        )
    elif provider_name == "deterministic":
        provider = DeterministicProvider()
    elif provider_name == "cloud":
        provider = CloudAIProvider()
    else:
        raise AppError(
            400,
            "unknown_provider",
            title="Unknown provider",
            detail=f"Provider '{provider_name}' is not supported.",
        )

    health = await provider.health()
    models = await provider.list_models()
    return ProviderInfoResponse(
        name=provider_name,
        healthy=health["healthy"],
        detail=health["detail"],
        models=health.get("models", models),
    )
