"""Database-backed authentication, session and password-reset services."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.parse import quote
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import Request
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.errors import AppError
from app.core.config import get_settings
from app.core.security import (
    generate_token,
    hash_token,
    issue_csrf_token,
    perform_dummy_password_check,
    verify_password_async,
)
from app.db.models import PasswordResetToken, User, UserSession, UserSettings
from app.schemas.auth import SessionResponse, UserResponse, UserSettingsResponse

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IssuedSession:
    raw_token: str
    csrf_token: str
    record: UserSession


@dataclass(frozen=True)
class CurrentAuth:
    user: User
    session: UserSession
    raw_token: str


def utcnow() -> datetime:
    return datetime.now(UTC)


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def request_metadata(request: Request) -> tuple[str | None, str | None]:
    user_agent = request.headers.get("user-agent")
    if user_agent:
        user_agent = user_agent.strip()[:512] or None
    client_host = request.client.host if request.client else None
    return user_agent, client_host


def serialize_user(user: User) -> UserResponse:
    settings = user.settings
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        email_verified=user.email_verified_at is not None,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        settings=UserSettingsResponse(
            timezone=settings.timezone if settings else "UTC",
            week_starts_on=settings.week_starts_on if settings else 0,
        ),
    )


def serialize_session(session: UserSession, current_session_id: uuid.UUID) -> SessionResponse:
    return SessionResponse(
        id=session.id,
        created_at=session.created_at,
        last_used_at=session.last_used_at,
        expires_at=session.expires_at,
        user_agent=session.user_agent,
        ip_address=session.ip_address,
        current=session.id == current_session_id,
    )


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(
        select(User)
        .where(User.email == email.strip().lower())
        .options(selectinload(User.settings))
    )
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    *,
    email: str,
    password_hash: str,
    full_name: str | None,
) -> User:
    user = User(email=email.strip().lower(), password_hash=password_hash, full_name=full_name)
    db.add(user)
    try:
        await db.flush()
        db.add(UserSettings(user_id=user.id))
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise AppError(
            409,
            "email_already_registered",
            title="Account already exists",
            detail="An account with this email already exists. Try signing in instead.",
        ) from exc

    await db.refresh(user, attribute_names=["settings"])
    return user


async def create_session(
    db: AsyncSession,
    *,
    user: User,
    request: Request,
    now: datetime | None = None,
) -> IssuedSession:
    settings = get_settings()
    now = now or utcnow()
    session_id = uuid.uuid4()
    raw_token = generate_token()
    csrf_token = issue_csrf_token(session_id)
    user_agent, ip_address = request_metadata(request)
    expires_at = now + timedelta(days=settings.session_ttl_days)

    record = UserSession(
        id=session_id,
        user_id=user.id,
        token_hash=hash_token(raw_token),
        csrf_token_hash=hash_token(csrf_token),
        user_agent=user_agent,
        ip_address=ip_address,
        expires_at=expires_at,
        last_used_at=now,
    )
    db.add(record)
    await db.flush()
    return IssuedSession(raw_token=raw_token, csrf_token=csrf_token, record=record)


async def revoke_token_if_present(
    db: AsyncSession,
    token: str | None,
) -> UserSession | None:
    if not token:
        return None
    result = await db.execute(
        select(UserSession).where(
            UserSession.token_hash == hash_token(token),
            UserSession.revoked_at.is_(None),
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        return None
    session.revoked_at = utcnow()
    return session


async def resolve_session(
    db: AsyncSession,
    token: str | None,
) -> CurrentAuth | None:
    if not token:
        return None

    result = await db.execute(
        select(UserSession)
        .where(
            UserSession.token_hash == hash_token(token),
            UserSession.revoked_at.is_(None),
        )
        .options(selectinload(UserSession.user).selectinload(User.settings))
    )
    session = result.scalar_one_or_none()
    if session is None:
        return None

    now = utcnow()
    if _aware(session.expires_at) <= now:
        session.revoked_at = now
        await db.commit()
        return None

    if not session.user.is_active:
        session.revoked_at = now
        await db.commit()
        return None

    return CurrentAuth(user=session.user, session=session, raw_token=token)


async def touch_session(db: AsyncSession, auth: CurrentAuth) -> bool:
    """Extend a sliding session at most once per configured interval."""
    settings = get_settings()
    now = utcnow()
    last_used = _aware(auth.session.last_used_at or auth.session.created_at)
    if now - last_used < timedelta(minutes=settings.session_refresh_minutes):
        return False

    absolute_expiry = _aware(auth.session.created_at) + timedelta(
        days=settings.session_absolute_ttl_days
    )
    if now >= absolute_expiry:
        auth.session.revoked_at = now
        await db.commit()
        raise AppError(
            401,
            "session_expired",
            title="Session expired",
            detail="Your session has reached its maximum lifetime. Sign in again.",
        )

    auth.session.last_used_at = now
    auth.session.expires_at = min(
        now + timedelta(days=settings.session_ttl_days),
        absolute_expiry,
    )
    await db.commit()
    return True


async def authenticate(db: AsyncSession, *, email: str, password: str) -> User | None:
    user = await get_user_by_email(db, email)
    if user is None:
        await perform_dummy_password_check(password)
        return None

    password_valid = await verify_password_async(password, user.password_hash)
    if not password_valid or not user.is_active:
        return None
    return user


async def list_active_sessions(db: AsyncSession, *, user_id: uuid.UUID) -> list[UserSession]:
    now = utcnow()
    result = await db.execute(
        select(UserSession)
        .where(
            UserSession.user_id == user_id,
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > now,
        )
        .order_by(UserSession.created_at.desc())
    )
    return list(result.scalars().all())


async def revoke_session(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
) -> UserSession | None:
    result = await db.execute(
        select(UserSession).where(
            UserSession.id == session_id,
            UserSession.user_id == user_id,
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        return None
    if session.revoked_at is None:
        session.revoked_at = utcnow()
    await db.commit()
    return session


async def revoke_all_sessions(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    except_session_id: uuid.UUID | None = None,
) -> None:
    conditions = [UserSession.user_id == user_id, UserSession.revoked_at.is_(None)]
    if except_session_id is not None:
        conditions.append(UserSession.id != except_session_id)
    await db.execute(update(UserSession).where(*conditions).values(revoked_at=utcnow()))


async def create_password_reset(
    db: AsyncSession,
    *,
    user: User,
) -> tuple[str, PasswordResetToken]:
    settings = get_settings()
    now = utcnow()
    await db.execute(
        update(PasswordResetToken)
        .where(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.used_at.is_(None),
        )
        .values(used_at=now)
    )

    raw_token = generate_token()
    record = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_token(raw_token),
        expires_at=now + timedelta(minutes=settings.password_reset_ttl_minutes),
    )
    db.add(record)
    await db.flush()
    return raw_token, record


def password_reset_url(raw_token: str) -> str:
    base = get_settings().web_app_url.rstrip("/")
    return f"{base}/reset-password?token={quote(raw_token, safe='')}"


async def consume_password_reset(
    db: AsyncSession,
    *,
    raw_token: str,
    new_password_hash: str,
) -> None:
    now = utcnow()
    result = await db.execute(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == hash_token(raw_token),
            PasswordResetToken.used_at.is_(None),
            PasswordResetToken.expires_at > now,
        )
    )
    reset = result.scalar_one_or_none()
    if reset is None:
        raise AppError(
            400,
            "invalid_reset_token",
            title="Reset link is invalid",
            detail="This password reset link is invalid or has expired. Request a new one.",
        )

    reset.used_at = now
    await db.execute(
        update(User)
        .where(User.id == reset.user_id)
        .values(password_hash=new_password_hash, updated_at=now)
    )
    await revoke_all_sessions(db, user_id=reset.user_id)
    await db.execute(
        update(PasswordResetToken)
        .where(
            PasswordResetToken.user_id == reset.user_id,
            PasswordResetToken.used_at.is_(None),
        )
        .values(used_at=now)
    )
    await db.commit()
    logger.info("Password reset completed for user %s", reset.user_id)


def validate_timezone(value: str) -> str:
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise AppError(
            422,
            "invalid_timezone",
            title="Invalid timezone",
            detail="Choose a timezone from the IANA timezone database.",
        ) from exc
    return value
