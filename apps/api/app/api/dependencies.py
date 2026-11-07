"""Shared request dependencies: origin, cookies, sessions and CSRF checks."""

from __future__ import annotations

from datetime import timedelta
from urllib.parse import urlsplit

from fastapi import Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.errors import AppError
from app.core.config import get_settings
from app.core.cookies import set_csrf_cookie, set_session_cookie
from app.core.security import (
    constant_time_equals,
    hash_token,
    issue_csrf_token,
    verify_csrf_signature,
)
from app.db.models import User
from app.db.session import get_db_session
from app.services.auth import (
    CurrentAuth,
    IssuedSession,
    create_session,
    resolve_session,
    touch_session,
    utcnow,
)

_UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def unauthorized() -> AppError:
    return AppError(
        401,
        "not_authenticated",
        title="Authentication required",
        detail="Sign in to continue.",
    )


def csrf_failed() -> AppError:
    return AppError(
        403,
        "csrf_validation_failed",
        title="Request could not be verified",
        detail="Refresh the page and try again.",
    )


def _allowed_origins() -> set[str]:
    settings = get_settings()
    return {
        origin.rstrip("/")
        for origin in [*settings.cors_origin_list, settings.web_app_url]
        if origin
    }


async def validate_request_origin(request: Request) -> None:
    """Reject state-changing browser requests from unknown origins."""
    if request.method not in _UNSAFE_METHODS:
        return

    allowed = _allowed_origins()
    origin = request.headers.get("origin")
    if origin:
        if origin.rstrip("/") not in allowed:
            raise AppError(
                403,
                "origin_not_allowed",
                title="Request origin not allowed",
                detail="This request did not originate from the configured web application.",
            )
        return

    referer = request.headers.get("referer")
    if referer:
        parsed = urlsplit(referer)
        if parsed.scheme and parsed.netloc:
            candidate = f"{parsed.scheme}://{parsed.netloc}"
            if candidate in allowed:
                return

    raise AppError(
        403,
        "origin_required",
        title="Request origin required",
        detail="This request did not include a trusted origin.",
    )


async def get_optional_auth(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> CurrentAuth | None:
    settings = get_settings()
    return await resolve_session(db, request.cookies.get(settings.session_cookie_name))


async def get_current_auth(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
) -> CurrentAuth:
    settings = get_settings()
    token = request.cookies.get(settings.session_cookie_name)
    auth = await resolve_session(db, token)
    if auth is None:
        raise unauthorized()

    refreshed = await touch_session(db, auth)
    if refreshed:
        set_session_cookie(response, auth.raw_token, auth.session.expires_at)
    return auth


async def get_current_user(
    auth: CurrentAuth = Depends(get_current_auth),
) -> User:
    return auth.user


async def require_csrf(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
) -> None:
    """Signed double-submit CSRF validation, bound to the active session."""
    if request.method not in _UNSAFE_METHODS:
        return

    settings = get_settings()
    header = request.headers.get(settings.csrf_header_name)
    cookie = request.cookies.get(settings.csrf_cookie_name)
    if not header or not cookie or not constant_time_equals(header, cookie):
        raise csrf_failed()

    subject = verify_csrf_signature(header)
    if subject is None:
        raise csrf_failed()

    session_token = request.cookies.get(settings.session_cookie_name)
    if subject == "anon":
        if session_token:
            auth = await resolve_session(db, session_token)
            if auth is not None:
                raise csrf_failed()
        return

    if not session_token:
        raise csrf_failed()
    auth = await resolve_session(db, session_token)
    if auth is None:
        raise csrf_failed()
    if not constant_time_equals(subject, auth.session.id.hex):
        raise csrf_failed()
    if not constant_time_equals(hash_token(header), auth.session.csrf_token_hash):
        raise csrf_failed()


async def issue_session_for_response(
    *,
    db: AsyncSession,
    response: Response,
    user: User,
    request: Request,
) -> IssuedSession:
    issued = await create_session(db, user=user, request=request)
    set_session_cookie(response, issued.raw_token, issued.record.expires_at)
    set_csrf_cookie(response, issued.csrf_token, issued.record.expires_at)
    return issued


async def bootstrap_csrf(
    *,
    request: Request,
    response: Response,
    db: AsyncSession,
    auth: CurrentAuth | None,
) -> str:
    """Return a usable signed CSRF token, rotating only when necessary."""
    settings = get_settings()
    existing = request.cookies.get(settings.csrf_cookie_name)

    if auth is not None:
        if (
            existing
            and constant_time_equals(verify_csrf_signature(existing) or "", auth.session.id.hex)
            and constant_time_equals(hash_token(existing), auth.session.csrf_token_hash)
        ):
            return existing

        token = issue_csrf_token(auth.session.id)
        auth.session.csrf_token_hash = hash_token(token)
        await db.commit()
        set_csrf_cookie(response, token, auth.session.expires_at)
        return token

    if existing and verify_csrf_signature(existing) == "anon":
        return existing

    token = issue_csrf_token(None)
    set_csrf_cookie(response, token, utcnow() + timedelta(days=settings.session_ttl_days))
    return token
