"""Privacy, consent, export, deletion, and audit tests."""

from __future__ import annotations

import uuid

from app.db.models.user import User
from app.db.session import SessionFactory
from app.main import app
from httpx import ASGITransport, AsyncClient
from sqlalchemy import update

ORIGIN = "http://localhost:3000"
EMAIL_DOMAIN = "phase2.auvyren.app"
PASSWORD = "correct horse battery staple"
PRIVACY = "/api/v1/privacy"


def unique_email(prefix: str = "user") -> str:
    return f"{prefix}-{uuid.uuid4().hex}@{EMAIL_DOMAIN}"


def make_client() -> AsyncClient:
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
        headers={"Origin": ORIGIN, "Referer": f"{ORIGIN}/"},
    )


def csrf_headers(token: str) -> dict[str, str]:
    return {"X-CSRF-Token": token}


async def get_csrf(client: AsyncClient) -> str:
    response = await client.get("/api/v1/auth/csrf")
    assert response.status_code == 200, response.text
    return response.json()["csrf_token"]


async def auth_headers(client: AsyncClient) -> dict[str, str]:
    return csrf_headers(await get_csrf(client))


async def register(client: AsyncClient, *, email: str) -> None:
    token = await get_csrf(client)
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD, "full_name": "Privacy Test"},
        headers=csrf_headers(token),
    )
    assert response.status_code == 201, response.text


async def test_consent_grant_check_list_and_revoke(client: AsyncClient) -> None:
    await register(client, email=unique_email("consent"))
    headers = await auth_headers(client)

    created = await client.post(
        f"{PRIVACY}/consent/ollama",
        json={"provider": "ollama"},
        headers=headers,
    )
    assert created.status_code == 201, created.text
    assert created.json()["provider"] == "ollama"
    assert created.json()["granted_at"] is not None

    checked = await client.get(f"{PRIVACY}/consent/ollama/check")
    assert checked.status_code == 200
    assert checked.json() == {"granted": True, "provider": "ollama"}

    listed = await client.get(f"{PRIVACY}/consent")
    assert listed.status_code == 200
    assert [item["provider"] for item in listed.json()] == ["ollama"]

    revoked = await client.delete(f"{PRIVACY}/consent/ollama", headers=headers)
    assert revoked.status_code == 204

    after = await client.get(f"{PRIVACY}/consent/ollama/check")
    assert after.json()["granted"] is False


async def test_consent_is_scoped_to_the_authenticated_user(client: AsyncClient) -> None:
    await register(client, email=unique_email("consent-owner"))
    headers = await auth_headers(client)
    created = await client.post(
        f"{PRIVACY}/consent/deterministic",
        json={"provider": "deterministic"},
        headers=headers,
    )
    assert created.status_code == 201, created.text

    async with make_client() as other:
        await register(other, email=unique_email("consent-other"))
        other_headers = await auth_headers(other)

        check = await other.get(f"{PRIVACY}/consent/deterministic/check")
        assert check.status_code == 200
        assert check.json()["granted"] is False

        revoke = await other.delete(
            f"{PRIVACY}/consent/deterministic",
            headers=other_headers,
        )
        assert revoke.status_code == 404


async def test_consent_requires_csrf(client: AsyncClient) -> None:
    await register(client, email=unique_email("consent-csrf"))
    response = await client.post(
        f"{PRIVACY}/consent/ollama",
        json={"provider": "ollama"},
    )
    assert response.status_code == 403
    assert response.json()["code"] == "csrf_validation_failed"


async def test_data_export_request_list_get_and_readiness(client: AsyncClient) -> None:
    await register(client, email=unique_email("export"))
    headers = await auth_headers(client)

    created = await client.post(f"{PRIVACY}/export", json={}, headers=headers)
    assert created.status_code == 201, created.text
    assert created.json()["status"] == "pending"
    export_id = created.json()["id"]

    listed = await client.get(f"{PRIVACY}/export")
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [export_id]

    fetched = await client.get(f"{PRIVACY}/export/{export_id}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == export_id

    download = await client.get(f"{PRIVACY}/export/{export_id}/download")
    assert download.status_code == 400
    assert download.json()["code"] == "export_not_ready"


async def test_export_is_not_visible_to_another_user(client: AsyncClient) -> None:
    await register(client, email=unique_email("export-owner"))
    headers = await auth_headers(client)
    created = await client.post(f"{PRIVACY}/export", json={}, headers=headers)
    assert created.status_code == 201
    export_id = created.json()["id"]

    async with make_client() as other:
        await register(other, email=unique_email("export-other"))
        response = await other.get(f"{PRIVACY}/export/{export_id}")
        assert response.status_code == 404
        assert response.json()["code"] == "export_not_found"


async def test_account_deletion_requires_confirmation_token(client: AsyncClient) -> None:
    await register(client, email=unique_email("delete-token"))
    headers = await auth_headers(client)

    requested = await client.post(
        f"{PRIVACY}/account/delete",
        json={"reason": "Testing the confirmation gate"},
        headers=headers,
    )
    assert requested.status_code == 201, requested.text
    token = requested.json()["confirmation_token"]
    assert token
    assert requested.json()["status"] == "pending"

    wrong = await client.post(
        f"{PRIVACY}/account/delete/confirm",
        json={"confirmation_token": "not-the-token"},
        headers=headers,
    )
    assert wrong.status_code == 400
    assert wrong.json()["code"] == "invalid_confirmation_token"

    confirmed = await client.post(
        f"{PRIVACY}/account/delete/confirm",
        json={"confirmation_token": token},
        headers=headers,
    )
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["status"] == "confirmed"
    assert "confirmation_token" not in confirmed.json()


async def test_account_deletion_completes_and_revokes_access(client: AsyncClient) -> None:
    email = unique_email("delete-complete")
    await register(client, email=email)
    headers = await auth_headers(client)

    requested = await client.post(
        f"{PRIVACY}/account/delete",
        json={"reason": "No longer needed"},
        headers=headers,
    )
    assert requested.status_code == 201, requested.text
    token = requested.json()["confirmation_token"]

    confirmed = await client.post(
        f"{PRIVACY}/account/delete/confirm",
        json={"confirmation_token": token},
        headers=headers,
    )
    assert confirmed.status_code == 200, confirmed.text

    completed = await client.post(
        f"{PRIVACY}/account/delete/complete",
        headers=headers,
    )
    assert completed.status_code == 204, completed.text

    me = await client.get("/api/v1/auth/me")
    assert me.status_code == 401

    async with SessionFactory() as db:
        result = await db.execute(update(User).where(User.email == email).values(is_active=True))
        assert result.rowcount == 0


async def test_privacy_actions_are_audited(client: AsyncClient) -> None:
    await register(client, email=unique_email("audit"))
    headers = await auth_headers(client)

    granted = await client.post(
        f"{PRIVACY}/consent/ollama",
        json={"provider": "ollama"},
        headers=headers,
    )
    assert granted.status_code == 201

    events = await client.get(f"{PRIVACY}/audit")
    assert events.status_code == 200
    event_types = [event["event_type"] for event in events.json()]
    assert "ai.consent.granted" in event_types

    filtered = await client.get(
        f"{PRIVACY}/audit",
        params={"event_type": "ai.consent.granted"},
    )
    assert filtered.status_code == 200
    assert len(filtered.json()) == 1


async def test_inactive_user_cannot_reach_protected_routes(client: AsyncClient) -> None:
    email = unique_email("inactive")
    await register(client, email=email)
    headers = await auth_headers(client)

    async with SessionFactory() as db:
        await db.execute(update(User).where(User.email == email).values(is_active=False))
        await db.commit()

    for path in ("/api/v1/tasks", "/api/v1/goals", "/api/v1/knowledge"):
        response = await client.get(path)
        assert response.status_code == 401, f"GET {path} returned {response.status_code}"

    post = await client.post("/api/v1/tasks", json={}, headers=headers)
    assert post.status_code in {401, 403}
