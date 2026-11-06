import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import AppError
from app.core.config import get_settings
from app.db.session import get_db_session
from app.schemas.health import HealthResponse, ReadinessResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["System"])


@router.get(
    "/health/live",
    response_model=HealthResponse,
    summary="Liveness probe",
    description="Returns OK when the API process is running. Does not touch the database.",
)
async def liveness() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="ok", service=settings.app_name, version=settings.app_version)


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    summary="Readiness probe",
    description="Returns OK only when the API can successfully query PostgreSQL.",
)
async def readiness(
    session: AsyncSession = Depends(get_db_session),
) -> ReadinessResponse:
    settings = get_settings()
    try:
        await session.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        logger.warning("Database readiness check failed: %s", type(exc).__name__)
        raise AppError(
            503,
            "database_unavailable",
            title="Service unavailable",
            detail="The database is not reachable.",
        ) from exc

    return ReadinessResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
        database="ok",
    )
