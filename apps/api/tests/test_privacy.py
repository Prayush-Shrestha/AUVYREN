"""Phase 6: Privacy, Consent, Export, and Deletion tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from app.db.models.auth import UserSession
from app.db.models.privacy import AIConsent, AccountDeletion, DataExport
from app.db.session import SessionFactory
from app.main import app
from httpx import ASGITransport, AsyncClient

ORIGIN = "http://localhost:3000"
EMAIL_DOMAIN = "phase6.auvyren.app"
PASSWORD = "correct horse battery staple"


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
    response = await client.get("/api/v1/auth/csrf")
    assert response.status_code == 200, response.text
    return response.json()["csrf_token"]


async def register(
    client: AsyncClient,
    *,
    email: str | None = None,
    password: str = PASSWORD,
    full_name: str | None = "Phase Six",
):
    token = await get_csrf(client)
    return await client.post(
        "/api/v1/auth/register",
        json={"email": email or unique_email(), "password": password, "full_name": full_name},
        headers=csrf_headers(token),
    )


async def login(client: AsyncClient, email: str, password: str):
    token = await get_csrf(client)
    return await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
        headers=csrf_headers(token),
    )


async def auth_headers(client: AsyncClient) -> dict[str, str]:
    return csrf_headers(await get_csrf(client))


async def test_consent_grant_and_revoke(client: AsyncClient) -> None:
    """Test consent grant and revoke for AI providers."""
    email = unique_email("consent")
    created = await register(client, email=email)
    assert created.status_code == 201
    headers = await auth_headers(client)

    # Grant consent for Ollama
    response = await client.post(
        "/privacy/consent/ollama",
        json={"provider": "ollama"},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    assert response.json()["provider"] == "ollama"
    assert response.json()["granted_at"] is not None

    # Check consent status
    check = await client.get(
        "/privacy/consent/ollama/check",
        headers=headers,
    )
    assert check.status_code == 200
    assert check.json()["granted"] is True

    # List consents
    listed = await client.get("/privacy/consent", headers=headers)
    assert listed.status_code == 200
    consents = listed.json()
    assert len(consents) == 1
    assert consents[0]["provider"] == "ollama"

    # Revoke consent
    revoked = await client.delete(
        "/privacy/consent/ollama",
        headers=headers,
    )
    assert revoked.status_code == 204

    # Verify revoked
    checked = await client.get(
        "/privacy/consent/ollama/check",
        headers=headers,
    )
    assert checked.status_code == 200
    assert checked.json()["granted"] is False


async def test_cross_user_consent_isolation(client: AsyncClient) -> None:
    """Test that users cannot access each other's consent."""
    email1 = unique_email("consent1")
    email2 = unique_email("consent2")

    created1 = await register(client, email=email1)
    assert created1.status_code == 201
    headers1 = await auth_headers(client)

    # Client 2
    client2 = make_client()
    created2 = await register(client2, email=email2)
    assert created2.status_code == 201
    headers2 = await auth_headers(client2)

    # Client 1 grants consent
    await client.post(
        "/privacy/consent/ollama",
        json={"provider": "ollama"},
        headers=headers1,
    )

    # Client 2 tries to access client 1's consent - should fail
    cross = await client2.get(
        "/privacy/consent/ollama/check",
        headers=headers2,
    )
    # Client 2 hasn't granted consent, so this should return granted=false
    assert checked.status_code == 200
    assert checked.json()["granted"] is False


async def test_data_export_request(client: AsyncClient) -> None:
    """Test data export request."""
    email = unique_email("export")
    created = await register(client, email=email)
    assert created.status_code == 201
    headers = await auth_headers(client)

    # Request export
    response = await client.post(
        "/privacy/export",
        json={},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    assert response.json()["status"] == "pending"
    assert response.json()["user_id"] is not None

    # List exports
    listed = await client.get("/privacy/export", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["status"] == "pending"

    # Get specific export
    export_id = listed.json()[0]["id"]
    fetched = await client.get(
        f"/privacy/export/{export_id}",
        headers=headers,
    )
    assert fetched.status_code == 200
    assert fetched.json()["id"] == export_id


async def test_cross_user_export_access(client: AsyncClient) -> None:
    """Test cross-user export access returns 404."""
    email1 = unique_email("export1")
    email2 = unique_email("export2")

    created1 = await register(client, email=email1)
    assert created1.status_code == 201
    headers1 = await auth_headers(client)

    created2 = await register(client, email=email2)
    assert created2.status_code == 201
    headers2 = await auth_headers(client)

    # Client 1 exports
    export = await client.post(
        "/privacy/export",
        json={},
        headers=headers1,
    )
    assert export.status_code == 201
    export_id = export.json()["id"]

    # Client 2 tries to access client 1's export
    cross = await client2.get(
        f"/privacy/export/{export_id}",
        headers=headers2,
    )
    assert cross.status_code == 404


async def test_account_deletion_request(client: AsyncClient) -> None:
    """Test account deletion request flow."""
    email = unique_email("delete")
    created = await register(client, email=email)
    assert created.status_code == 201
    headers = await auth_headers(client)

    # Request deletion
    response = await client.post(
        "/privacy/account/delete",
        json={"reason": "No longer needed"},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    assert response.json()["status"] == "pending"
    assert response.json()["confirmation_token"] is not None

    # Confirm deletion
    confirmation_token = response.json()["confirmation_token"]
    confirmed = await client.post(
        "/privacy/account/delete/confirm",
        json={"confirmation_token": confirmation_token},
        headers=headers,
    )
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["status"] == "confirmed"

    # Complete deletion
    completed = await client.post(
        "/privacy/account/delete/complete",
        headers=headers,
    )
    assert completed.status_code == 204

    # Verify user cannot access anymore
    me = await client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 401


async def test_audit_events_logged(client: AsyncClient) -> None:
    """Test that audit events are logged for auth actions."""
    email = unique_email("audit")
    created = await register(client, email=email)
    assert created.status_code == 201
    headers = await auth_headers(client)

    # Perform some actions that should be audited
    await client.get("/api/v1/auth/me", headers=headers)
    await client.get("/api/v1/auth/sessions", headers=headers)

    # List audit events - should have at least some entries
    audits = await client.get("/privacy/audit", headers=headers)
    assert audits.status_code == 200
    assert len(audits.json()) > 0


async def test_inactive_user_cannot_access_productivity(client: AsyncClient) -> None:
    """Test that inactive users cannot access productivity endpoints."""
    email = unique_email("inactive")
    created = await register(client, email=email)
    assert created.status_code == 201
    headers = await auth_headers(client)

    # Deactivate user in DB
    from app.db.models.user import User
    from app.db.session import SessionFactory
    async with SessionFactory() as db:
        from sqlalchemy import update
        await db.execute(update(User).where(User.email == email).values(is_active=False))
        await db.commit()

    # All productivity endpoints should return 401
    endpoints = [
        ("GET", "/api/v1/tasks"),
        ("POST", "/api/v1/tasks"),
        ("GET", "/api/v1/goals"),
        ("POST", "/api/v1/goals"),
        ("GET", "/api/v1/projects"),
        ("POST", "/api/v1/projects"),
        ("GET", "/api/v1/habits"),
        ("POST", "/api/v1/habits"),
        ("GET", "/api/v1/calendar"),
        ("POST", "/api/v1/calendar"),
        ("GET", "/api/v1/routines"),
        ("POST", "/api/v1/routines"),
    ]
    for method, path in endpoints:
        if method == "GET":
            response = await client.get(path, headers=headers)
        else:
            response = await client.post(path, json={}, headers=headers)
        assert response.status_code == 401, f"{method} {path} returned {response.status_code}"
