from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlparse

import pytest
from app.api.v1.routes import auth as auth_routes
from app.core.security import hash_token
from app.db.models import PasswordResetToken, User, UserSession
from app.db.session import SessionFactory
from app.main import app
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, update

ORIGIN = "http://localhost:3000"
EMAIL_DOMAIN = "phase2.auvyren.app"
PASSWORD = "correct horse battery staple"
NEW_PASSWORD = "a quieter and longer passphrase"
REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"
LOGOUT = "/api/v1/auth/logout"
ME = "/api/v1/auth/me"
CSRF = "/api/v1/auth/csrf"
FORGOT = "/api/v1/auth/forgot-password"
RESET = "/api/v1/auth/reset-password"
SESSIONS = "/api/v1/auth/sessions"


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
    response = await client.get(CSRF)
    assert response.status_code == 200, response.text
    return response.json()["csrf_token"]


async def register(
    client: AsyncClient,
    *,
    email: str | None = None,
    password: str = PASSWORD,
    full_name: str | None = "Phase Two",
):
    token = await get_csrf(client)
    return await client.post(
        REGISTER,
        json={"email": email or unique_email(), "password": password, "full_name": full_name},
        headers=csrf_headers(token),
    )


async def login(client: AsyncClient, email: str, password: str):
    token = await get_csrf(client)
    return await client.post(
        LOGIN,
        json={"email": email, "password": password},
        headers=csrf_headers(token),
    )


async def auth_headers(client: AsyncClient) -> dict[str, str]:
    return csrf_headers(await get_csrf(client))


async def test_registration_hashes_password_and_sets_secure_cookies(client: AsyncClient) -> None:
    email = unique_email("register")
    response = await register(client, email=email)

    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["user"]["email"] == email
    assert payload["user"]["full_name"] == "Phase Two"
    assert payload["user"]["settings"] == {"timezone": "UTC", "week_starts_on": 0}
    assert payload["csrf_token"].startswith("v1.")
    assert PASSWORD not in response.text
    assert "password_hash" not in response.text

    raw_session = client.cookies.get("auv_session")
    assert raw_session
    assert client.cookies.get("auv_csrf") == payload["csrf_token"]

    cookie_headers = response.headers.get_list("set-cookie")
    session_cookie = next(item for item in cookie_headers if item.startswith("auv_session="))
    csrf_cookie = next(item for item in cookie_headers if item.startswith("auv_csrf="))
    assert "httponly" in session_cookie.lower()
    assert "samesite=lax" in session_cookie.lower()
    assert "httponly" not in csrf_cookie.lower()

    async with SessionFactory() as db:
        user = (
            await db.execute(select(User).where(User.email == email))
        ).scalar_one()
        assert user.password_hash.startswith("$argon2id$")
        assert hash_token(raw_session) != raw_session
        session = (
            await db.execute(select(UserSession).where(UserSession.user_id == user.id))
        ).scalar_one()
        assert session.token_hash == hash_token(raw_session)
        assert session.csrf_token_hash == hash_token(payload["csrf_token"])


async def test_registration_normalizes_email_and_rejects_duplicates(client: AsyncClient) -> None:
    email = unique_email("normalize")
    mixed_case = email.replace("normalize-", "NORMALIZE-").upper()
    first = await register(client, email=mixed_case)
    assert first.status_code == 201, first.text
    assert first.json()["user"]["email"] == email.lower()

    duplicate = await register(client, email=email.upper())
    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "email_already_registered"


async def test_login_is_enumeration_safe_and_rotates_the_session(client: AsyncClient) -> None:
    email = unique_email("login")
    created = await register(client, email=email)
    assert created.status_code == 201
    old_session = client.cookies.get("auv_session")
    assert old_session

    wrong_password = await login(client, email, "this is not the password")
    assert wrong_password.status_code == 401
    unknown_email = await login(client, unique_email("unknown"), PASSWORD)
    assert unknown_email.status_code == 401

    assert wrong_password.json()["code"] == unknown_email.json()["code"]
    assert wrong_password.json()["detail"] == unknown_email.json()["detail"]

    signed_in = await login(client, email, PASSWORD)
    assert signed_in.status_code == 200, signed_in.text
    new_session = client.cookies.get("auv_session")
    assert new_session and new_session != old_session
    assert signed_in.json()["user"]["last_login_at"] is not None

    async with make_client() as stale:
        stale.cookies.set("auv_session", old_session)
        rejected = await stale.get(ME, headers=await auth_headers(stale))
    assert rejected.status_code == 401


async def test_session_cookie_is_required_for_profile_access(client: AsyncClient) -> None:
    response = await client.get(ME)
    assert response.status_code == 401
    assert response.json()["code"] == "not_authenticated"


async def test_csrf_is_signed_double_submit_and_bound_to_the_session(
    client: AsyncClient,
) -> None:
    created = await register(client)
    assert created.status_code == 201
    token = created.json()["csrf_token"]

    reused = await get_csrf(client)
    assert reused == token

    missing = await client.patch(ME, json={"full_name": "No token"}, headers={})
    assert missing.status_code == 403
    assert missing.json()["code"] == "csrf_validation_failed"

    wrong = await client.patch(
        ME,
        json={"full_name": "No token"},
        headers={"X-CSRF-Token": f"v1.anon.{uuid.uuid4().hex}.invalid"},
    )
    assert wrong.status_code == 403

    accepted = await client.patch(
        ME,
        json={"full_name": "With token"},
        headers=csrf_headers(token),
    )
    assert accepted.status_code == 200
    assert accepted.json()["full_name"] == "With token"


async def test_origin_and_csrf_guards_reject_untrusted_mutations() -> None:
    async with make_client(origin=None) as missing_origin:
        token = await get_csrf(missing_origin)
        response = await missing_origin.post(
            REGISTER,
            json={"email": unique_email("origin"), "password": PASSWORD},
            headers=csrf_headers(token),
        )
    assert response.status_code == 403
    assert response.json()["code"] == "origin_required"

    async with make_client(origin="https://evil.example") as evil_origin:
        response = await evil_origin.post(
            REGISTER,
            json={"email": unique_email("evil"), "password": PASSWORD},
        )
    assert response.status_code == 403
    assert response.json()["code"] == "origin_not_allowed"

    async with make_client() as no_csrf:
        response = await no_csrf.post(
            REGISTER,
            json={"email": unique_email("no-csrf"), "password": PASSWORD},
        )
    assert response.status_code == 403
    assert response.json()["code"] == "csrf_validation_failed"


async def test_profile_settings_are_real_and_validated(client: AsyncClient) -> None:
    created = await register(client)
    assert created.status_code == 201
    headers = await auth_headers(client)

    updated = await client.patch(
        ME,
        json={"full_name": "Ada Lovelace", "timezone": "Asia/Kathmandu", "week_starts_on": 1},
        headers=headers,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["full_name"] == "Ada Lovelace"
    assert updated.json()["settings"] == {"timezone": "Asia/Kathmandu", "week_starts_on": 1}

    invalid = await client.patch(
        ME,
        json={"timezone": "Mars/Olympus_Mons"},
        headers=headers,
    )
    assert invalid.status_code == 422
    assert invalid.json()["code"] == "invalid_timezone"

    cleared = await client.patch(ME, json={"full_name": None}, headers=headers)
    assert cleared.status_code == 200
    assert cleared.json()["full_name"] is None

    current = await client.get(ME)
    assert current.status_code == 200
    assert current.json()["settings"]["timezone"] == "Asia/Kathmandu"


async def test_logout_revokes_and_clears_the_session(client: AsyncClient) -> None:
    created = await register(client)
    assert created.status_code == 201
    raw_session = client.cookies.get("auv_session")
    token = created.json()["csrf_token"]
    assert raw_session

    response = await client.post(LOGOUT, headers=csrf_headers(token))
    assert response.status_code == 204
    assert client.cookies.get("auv_session") is None
    assert client.cookies.get("auv_csrf") is None

    async with make_client() as stale:
        stale.cookies.set("auv_session", raw_session)
        rejected = await stale.get(ME)
    assert rejected.status_code == 401

    async with SessionFactory() as db:
        session = (
            await db.execute(
                select(UserSession).where(UserSession.token_hash == hash_token(raw_session))
            )
        ).scalar_one()
        assert session.revoked_at is not None


async def test_session_listing_and_cross_user_revocation(client: AsyncClient) -> None:
    email = unique_email("sessions")
    created = await register(client, email=email)
    assert created.status_code == 201

    a_token = created.json()["csrf_token"]
    async with make_client() as second_client:
        signed_in = await login(second_client, email, PASSWORD)
        assert signed_in.status_code == 200, signed_in.text

        listed = await client.get(SESSIONS)
        assert listed.status_code == 200
        sessions = listed.json()["sessions"]
        assert len(sessions) == 2
        assert sum(1 for item in sessions if item["current"]) == 1
        current = next(item for item in sessions if item["current"])
        other = next(item for item in sessions if not item["current"])

        async with make_client() as stranger:
            stranger_registered = await register(stranger)
            assert stranger_registered.status_code == 201
            forbidden = await stranger.delete(
                f"{SESSIONS}/{other['id']}",
                headers=await auth_headers(stranger),
            )
        assert forbidden.status_code == 404
        assert forbidden.json()["code"] == "session_not_found"
        assert (await second_client.get(ME)).status_code == 200

        revoked = await client.delete(
            f"{SESSIONS}/{other['id']}", headers=csrf_headers(a_token)
        )
        assert revoked.status_code == 204, revoked.text
        assert (await second_client.get(ME)).status_code == 401

        remaining = await client.get(SESSIONS)
        assert len(remaining.json()["sessions"]) == 1

        ended = await client.delete(
            f"{SESSIONS}/{current['id']}", headers=csrf_headers(a_token)
        )
        assert ended.status_code == 204, ended.text
        assert (await client.get(ME)).status_code == 401


async def test_expired_and_absolute_expired_sessions_are_rejected(
    client: AsyncClient,
) -> None:
    created = await register(client)
    assert created.status_code == 201
    expired_raw = client.cookies.get("auv_session")
    assert expired_raw

    async with SessionFactory() as db:
        await db.execute(
            update(UserSession)
            .where(UserSession.token_hash == hash_token(expired_raw))
            .values(expires_at=datetime.now(UTC) - timedelta(minutes=1))
        )
        await db.commit()

    expired = await client.get(ME)
    assert expired.status_code == 401

    async with SessionFactory() as db:
        session = (
            await db.execute(
                select(UserSession).where(UserSession.token_hash == hash_token(expired_raw))
            )
        ).scalar_one()
        assert session.revoked_at is not None

    async with make_client() as absolute_client:
        registered = await register(absolute_client)
        assert registered.status_code == 201
        raw_session = absolute_client.cookies.get("auv_session")
        assert raw_session
        now = datetime.now(UTC)
        async with SessionFactory() as db:
            await db.execute(
                update(UserSession)
                .where(UserSession.token_hash == hash_token(raw_session))
                .values(
                    created_at=now - timedelta(days=91),
                    last_used_at=now - timedelta(minutes=10),
                    expires_at=now + timedelta(days=10),
                )
            )
            await db.commit()

        expired_absolute = await absolute_client.get(ME)
        assert expired_absolute.status_code == 401
        assert expired_absolute.json()["code"] == "session_expired"


async def test_forgot_password_is_generic_and_reset_is_single_use(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[dict[str, str | None]] = []

    async def fake_send_password_reset_email(**kwargs: str | None) -> None:
        captured.append(kwargs)

    monkeypatch.setattr(auth_routes, "send_password_reset_email", fake_send_password_reset_email)

    email = unique_email("reset")
    created = await register(client, email=email)
    assert created.status_code == 201
    headers = csrf_headers(created.json()["csrf_token"])

    async with make_client() as second_client:
        second_login = await login(second_client, email, PASSWORD)
        assert second_login.status_code == 200
        second_session = second_client.cookies.get("auv_session")
    assert second_session

    known = await client.post(FORGOT, json={"email": email}, headers=headers)
    unknown = await client.post(FORGOT, json={"email": unique_email("missing")}, headers=headers)
    assert known.status_code == 202
    assert unknown.status_code == 202
    assert known.json() == unknown.json()
    assert len(captured) == 1

    reset_url = captured[0]["reset_url"]
    assert isinstance(reset_url, str)
    token = parse_qs(urlparse(reset_url).query)["token"][0]

    async with SessionFactory() as db:
        reset = (
            await db.execute(
                select(PasswordResetToken).where(
                    PasswordResetToken.token_hash == hash_token(token)
                )
            )
        ).scalar_one()
        assert reset.used_at is None
        assert token not in reset.token_hash

    reset_response = await client.post(
        RESET,
        json={"token": token, "password": NEW_PASSWORD},
        headers=headers,
    )
    assert reset_response.status_code == 200, reset_response.text
    async with make_client() as revoked_client:
        revoked_client.cookies.set("auv_session", second_session)
        assert (await revoked_client.get(ME)).status_code == 401
    assert client.cookies.get("auv_session") is None

    old_login = await login(client, email, PASSWORD)
    assert old_login.status_code == 401
    new_login = await login(client, email, NEW_PASSWORD)
    assert new_login.status_code == 200, new_login.text

    reuse = await client.post(
        RESET,
        json={"token": token, "password": PASSWORD},
        headers=csrf_headers(new_login.json()["csrf_token"]),
    )
    assert reuse.status_code == 400
    assert reuse.json()["code"] == "invalid_reset_token"

    still_new = await login(client, email, NEW_PASSWORD)
    assert still_new.status_code == 200


async def test_login_rate_limit_returns_retry_after(client: AsyncClient) -> None:
    email = unique_email("limited")
    token = await get_csrf(client)
    responses = []
    for _ in range(5):
        responses.append(
            await client.post(
                LOGIN,
                json={"email": email, "password": "wrong password value"},
                headers=csrf_headers(token),
            )
        )
    assert all(response.status_code == 401 for response in responses)

    limited = await client.post(
        LOGIN,
        json={"email": email, "password": "wrong password value"},
        headers=csrf_headers(token),
    )
    assert limited.status_code == 429
    assert limited.json()["code"] == "rate_limit_exceeded"
    assert int(limited.headers["Retry-After"]) >= 1


async def test_inactive_user_cannot_sign_in(client: AsyncClient) -> None:
    email = unique_email("inactive")
    created = await register(client, email=email)
    assert created.status_code == 201
    async with SessionFactory() as db:
        await db.execute(update(User).where(User.email == email).values(is_active=False))
        await db.commit()

    async with make_client() as other:
        response = await login(other, email, PASSWORD)
    assert response.status_code == 401
    assert response.json()["code"] == "invalid_credentials"


async def test_password_reset_link_points_at_configured_web_origin(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[str] = []

    async def fake_send(**kwargs: str | None) -> None:
        captured.append(kwargs["reset_url"])

    monkeypatch.setattr(auth_routes, "send_password_reset_email", fake_send)
    created = await register(client)
    assert created.status_code == 201
    response = await client.post(
        FORGOT,
        json={"email": created.json()["user"]["email"]},
        headers=csrf_headers(created.json()["csrf_token"]),
    )
    assert response.status_code == 202
    assert captured[0].startswith("http://localhost:3000/reset-password?token=")
    assert "reset-password?token=" not in response.text


async def test_auth_responses_are_not_cacheable(client: AsyncClient) -> None:
    csrf = await client.get(CSRF)
    assert csrf.status_code == 200
    assert csrf.headers["Cache-Control"] == "no-store"

    created = await register(client)
    assert created.status_code == 201
    assert created.headers["Cache-Control"] == "no-store"

    me = await client.get(ME)
    assert me.status_code == 200
    assert me.headers["Cache-Control"] == "no-store"
