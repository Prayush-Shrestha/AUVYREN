"""Authentication, profile and session-management endpoints."""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    bootstrap_csrf,
    get_current_auth,
    get_optional_auth,
    issue_session_for_response,
    require_csrf,
)
from app.api.errors import AppError
from app.core.config import get_settings
from app.core.cookies import clear_csrf_cookie, clear_session_cookie
from app.core.rate_limit import (
    RateLimitRule,
    client_rate_key,
    email_rate_key,
    rate_limiter,
)
from app.core.security import hash_password_async
from app.db.models import UserSettings
from app.db.session import get_db_session
from app.schemas.auth import (
    AuthResponse,
    CsrfResponse,
    ForgotPasswordRequest,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    ResetPasswordRequest,
    SessionListResponse,
    UpdateProfileRequest,
    UserResponse,
)
from app.services.auth import (
    CurrentAuth,
    authenticate,
    consume_password_reset,
    create_password_reset,
    create_user,
    get_user_by_email,
    list_active_sessions,
    password_reset_url,
    revoke_session,
    revoke_token_if_present,
    serialize_session,
    serialize_user,
    utcnow,
    validate_timezone,
)
from app.services.email import send_password_reset_email

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    dependencies=[Depends(require_csrf)],
)

RESET_RESPONSE = "If an account exists for that email, a reset link has been sent."


def _client_host(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _ip_rule(prefix: str, request: Request, limit: int, window_seconds: int) -> RateLimitRule:
    return RateLimitRule(client_rate_key(prefix, _client_host(request)), limit, window_seconds)


def _email_rule(prefix: str, email: str, limit: int, window_seconds: int) -> RateLimitRule:
    return RateLimitRule(email_rate_key(prefix, email), limit, window_seconds)


@router.get("/csrf", response_model=CsrfResponse, summary="Bootstrap a CSRF token")
async def csrf_token(
    request: Request,
    response: Response,
    auth: CurrentAuth | None = Depends(get_optional_auth),
    db: AsyncSession = Depends(get_db_session),
) -> CsrfResponse:
    token = await bootstrap_csrf(request=request, response=response, db=db, auth=auth)
    return CsrfResponse(csrf_token=token)


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an account",
)
async def register(
    payload: RegisterRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
) -> AuthResponse:
    await rate_limiter.enforce([_ip_rule("register", request, 5, 60 * 60)])

    if await get_user_by_email(db, payload.email) is not None:
        raise AppError(
            409,
            "email_already_registered",
            title="Account already exists",
            detail="An account with this email already exists. Try signing in instead.",
        )

    password_hash = await hash_password_async(payload.password)
    user = await create_user(
        db,
        email=payload.email,
        password_hash=password_hash,
        full_name=payload.full_name,
    )

    settings = get_settings()
    await revoke_token_if_present(db, request.cookies.get(settings.session_cookie_name))
    issued = await issue_session_for_response(
        db=db,
        response=response,
        user=user,
        request=request,
    )
    await db.commit()

    logger.info("Account registered for user %s", user.id)
    return AuthResponse(user=serialize_user(user), csrf_token=issued.csrf_token)


@router.post("/login", response_model=AuthResponse, summary="Sign in")
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
) -> AuthResponse:
    await rate_limiter.enforce(
        [
            _ip_rule("login", request, 10, 15 * 60),
            _email_rule("login", payload.email, 5, 15 * 60),
        ]
    )

    user = await authenticate(db, email=payload.email, password=payload.password)
    if user is None:
        logger.warning("Failed sign-in attempt from %s", _client_host(request))
        raise AppError(
            401,
            "invalid_credentials",
            title="Sign-in failed",
            detail="Email or password is incorrect.",
        )

    settings = get_settings()
    await revoke_token_if_present(db, request.cookies.get(settings.session_cookie_name))
    user.last_login_at = utcnow()
    issued = await issue_session_for_response(
        db=db,
        response=response,
        user=user,
        request=request,
    )
    await db.commit()

    logger.info("Successful sign-in for user %s", user.id)
    return AuthResponse(user=serialize_user(user), csrf_token=issued.csrf_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Sign out")
async def logout(
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    auth.session.revoked_at = utcnow()
    await db.commit()
    clear_session_cookie(response)
    clear_csrf_cookie(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    logger.info("Session revoked for user %s", auth.user.id)


@router.get("/me", response_model=UserResponse, summary="Current account")
async def get_me(auth: CurrentAuth = Depends(get_current_auth)) -> UserResponse:
    return serialize_user(auth.user)


@router.patch("/me", response_model=UserResponse, summary="Update profile and preferences")
async def update_me(
    payload: UpdateProfileRequest,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> UserResponse:
    fields = payload.model_fields_set
    user = auth.user

    if "full_name" in fields:
        user.full_name = payload.full_name

    if "timezone" in fields or "week_starts_on" in fields:
        if user.settings is None:
            user.settings = UserSettings(user_id=user.id)
            db.add(user.settings)
        if "timezone" in fields and payload.timezone is not None:
            user.settings.timezone = validate_timezone(payload.timezone)
        if "week_starts_on" in fields and payload.week_starts_on is not None:
            user.settings.week_starts_on = payload.week_starts_on

    await db.commit()
    await db.refresh(user, attribute_names=["settings"])
    return serialize_user(user)


@router.get("/sessions", response_model=SessionListResponse, summary="List active sessions")
async def get_sessions(
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> SessionListResponse:
    sessions = await list_active_sessions(db, user_id=auth.user.id)
    return SessionListResponse(
        sessions=[serialize_session(item, auth.session.id) for item in sessions]
    )


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke a session",
)
async def delete_session(
    session_id: uuid.UUID,
    response: Response,
    auth: CurrentAuth = Depends(get_current_auth),
    db: AsyncSession = Depends(get_db_session),
) -> None:
    revoked = await revoke_session(db, user_id=auth.user.id, session_id=session_id)
    if revoked is None:
        raise AppError(
            404,
            "session_not_found",
            title="Session not found",
            detail="That session does not exist or has already ended.",
        )

    if revoked.id == auth.session.id:
        clear_session_cookie(response)
        clear_csrf_cookie(response)
    response.status_code = status.HTTP_204_NO_CONTENT
    logger.info("Session %s revoked for user %s", session_id, auth.user.id)


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request a password reset link",
)
async def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
) -> MessageResponse:
    await rate_limiter.enforce(
        [
            _ip_rule("forgot", request, 10, 60 * 60),
            _email_rule("forgot", payload.email, 5, 60 * 60),
        ]
    )

    user = await get_user_by_email(db, payload.email)
    if user is not None and user.is_active:
        raw_token, _ = await create_password_reset(db, user=user)
        await db.commit()
        background_tasks.add_task(
            send_password_reset_email,
            to_email=user.email,
            display_name=user.full_name,
            reset_url=password_reset_url(raw_token),
        )

    return MessageResponse(message=RESET_RESPONSE)


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Complete a password reset",
)
async def reset_password(
    payload: ResetPasswordRequest,
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> MessageResponse:
    await rate_limiter.enforce([_ip_rule("reset", request, 10, 60 * 60)])

    password_hash = await hash_password_async(payload.password)
    await consume_password_reset(db, raw_token=payload.token, new_password_hash=password_hash)
    clear_session_cookie(response)
    clear_csrf_cookie(response)
    return MessageResponse(
        message="Your password has been reset. Sign in with your new password."
    )
