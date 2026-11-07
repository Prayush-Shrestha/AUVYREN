"""Browser cookie helpers shared by authentication routes and dependencies."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import Response

from app.core.config import get_settings

_SAME_SITE = "lax"
_PATH = "/"


def _max_age(expires_at: datetime) -> int:
    remaining = expires_at - datetime.now(UTC)
    return max(0, int(remaining.total_seconds()))


def set_session_cookie(response: Response, token: str, expires_at: datetime) -> None:
    settings = get_settings()
    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=_max_age(expires_at),
        expires=expires_at,
        path=_PATH,
        domain=settings.session_cookie_domain,
        secure=settings.session_cookie_secure,
        httponly=True,
        samesite=_SAME_SITE,
    )


def clear_session_cookie(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(
        key=settings.session_cookie_name,
        path=_PATH,
        domain=settings.session_cookie_domain,
        secure=settings.session_cookie_secure,
        httponly=True,
        samesite=_SAME_SITE,
    )


def set_csrf_cookie(response: Response, token: str, expires_at: datetime) -> None:
    settings = get_settings()
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=token,
        max_age=_max_age(expires_at),
        expires=expires_at,
        path=_PATH,
        domain=settings.session_cookie_domain,
        secure=settings.session_cookie_secure,
        httponly=False,
        samesite=_SAME_SITE,
    )


def clear_csrf_cookie(response: Response) -> None:
    settings = get_settings()
    response.delete_cookie(
        key=settings.csrf_cookie_name,
        path=_PATH,
        domain=settings.session_cookie_domain,
        secure=settings.session_cookie_secure,
        httponly=False,
        samesite=_SAME_SITE,
    )
