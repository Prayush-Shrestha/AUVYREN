"""Sync tests: device registration, pull/push, conflict resolution, ownership."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from app.main import app
from httpx import ASGITransport, AsyncClient

ORIGIN = "http://localhost:3000"
EMAIL_DOMAIN = "phase7.auvyren.app"
PASSWORD = "correct horse battery staple"
SYNC = "/api/v1/sync"


_counter = 0

def unique_email(prefix: str = "sync") -> str:
    global _counter
    _counter += 1
    return f"{prefix}-{_counter}-{uuid.uuid4().hex}@{EMAIL_DOMAIN}"


def make_client() -> AsyncClient:
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
        headers={"Origin": ORIGIN, "Referer": f"{ORIGIN}/"},
    )


async def get_csrf(client: AsyncClient) -> str:
    response = await client.get("/api/v1/auth/csrf")
    assert response.status_code == 200, response.text
    return response.json()["csrf_token"]


async def register_user(client: AsyncClient, *, email: str | None = None) -> None:
    token = await get_csrf(client)
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email or unique_email(),
            "password": PASSWORD,
            "full_name": "Sync Test",
        },
        headers={"X-CSRF-Token": token},
    )
    assert response.status_code == 201, response.text


async def register_device(
    client: AsyncClient,
    *,
    device_id: str = "device-1",
    device_name: str | None = "Test Device",
    platform: str | None = "android",
    app_version: str | None = "1.0.0",
) -> dict:
    token = await get_csrf(client)
    response = await client.post(
        f"{SYNC}/devices",
        json={
            "device_id": device_id,
            "device_name": device_name,
            "platform": platform,
            "app_version": app_version,
        },
        headers={"X-CSRF-Token": token},
    )
    assert response.status_code == 201, response.text
    return response.json()


async def test_sync_requires_authentication(client: AsyncClient) -> None:
    assert (await client.get(f"{SYNC}/status")).status_code == 401
    assert (await client.get(f"{SYNC}/devices")).status_code == 401
    # POST is unsafe: CSRF is validated before authentication, so no CSRF -> 403.
    # With a valid CSRF token but no session -> 401.
    token = await get_csrf(client)
    response = await client.post(
        f"{SYNC}/devices",
        json={"device_id": "device-1"},
        headers={"X-CSRF-Token": token},
    )
    assert response.status_code == 401, response.text


async def test_register_and_list_device(client: AsyncClient) -> None:
    await register_user(client)
    device = await register_device(client)
    assert device["device_id"] == "device-1"
    assert device["device_name"] == "Test Device"
    assert device["platform"] == "android"
    assert device["app_version"] == "1.0.0"

    token = await get_csrf(client)
    response = await client.get(f"{SYNC}/devices", headers={"X-CSRF-Token": token})
    assert response.status_code == 200, response.text
    devices = response.json()
    assert len(devices) == 1
    assert devices[0]["device_id"] == "device-1"


async def test_register_device_requires_csrf(client: AsyncClient) -> None:
    await register_user(client)
    response = await client.post(f"{SYNC}/devices", json={"device_id": "device-1"})
    assert response.status_code == 403, response.text


async def test_unregister_device(client: AsyncClient) -> None:
    await register_user(client)
    await register_device(client, device_id="device-1")

    token = await get_csrf(client)
    response = await client.delete(
        f"{SYNC}/devices/device-1", headers={"X-CSRF-Token": token}
    )
    assert response.status_code == 204, response.text

    # List should now be empty
    response = await client.get(f"{SYNC}/devices", headers={"X-CSRF-Token": token})
    assert response.status_code == 200, response.text
    assert response.json() == []


async def test_unregister_nonexistent_device_returns_404(client: AsyncClient) -> None:
    await register_user(client)
    token = await get_csrf(client)
    response = await client.delete(
        f"{SYNC}/devices/nonexistent", headers={"X-CSRF-Token": token}
    )
    assert response.status_code == 404, response.text


async def test_sync_pull_empty(client: AsyncClient) -> None:
    await register_user(client)
    token = await get_csrf(client)
    response = await client.get(
        f"{SYNC}/pull", headers={"X-CSRF-Token": token}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["events"] == []
    assert "server_timestamp" in data


async def test_sync_push_and_pull(client: AsyncClient) -> None:
    await register_user(client)
    now = datetime.now(UTC).isoformat()

    # Push a create event
    token = await get_csrf(client)
    push_payload = {
        "events": [
            {
                "entity_type": "task",
                "entity_id": str(uuid.uuid4()),
                "action": "create",
                "revision": 1,
                "payload": {"title": "Synced task", "status": "todo"},
            }
        ],
        "client_timestamp": now,
    }
    response = await client.post(
        f"{SYNC}/push",
        json=push_payload,
        headers={"X-CSRF-Token": token},
    )
    assert response.status_code == 200, response.text
    push_result = response.json()
    assert push_result["applied"] == 1
    assert push_result["conflicts"] == []

    # Pull should return the event
    response = await client.get(f"{SYNC}/pull", headers={"X-CSRF-Token": token})
    assert response.status_code == 200, response.text
    pull_result = response.json()
    assert len(pull_result["events"]) == 1
    event = pull_result["events"][0]
    assert event["entity_type"] == "task"
    assert event["action"] == "create"
    assert event["revision"] == 1
    assert event["payload"]["title"] == "Synced task"


async def test_sync_conflict_resolution(client: AsyncClient) -> None:
    await register_user(client)

    # Push revision 1
    token = await get_csrf(client)
    entity_id = str(uuid.uuid4())
    response = await client.post(
        f"{SYNC}/push",
        json={
            "events": [
                {
                    "entity_type": "task",
                    "entity_id": entity_id,
                    "action": "create",
                    "revision": 1,
                    "payload": {"title": "v1"},
                }
            ]
        },
        headers={"X-CSRF-Token": token},
    )
    assert response.status_code == 200, response.text

    # Push revision 1 again (conflict: server already has revision 1)
    response = await client.post(
        f"{SYNC}/push",
        json={
            "events": [
                {
                    "entity_type": "task",
                    "entity_id": entity_id,
                    "action": "update",
                    "revision": 1,
                    "payload": {"title": "client_v1_conflict"},
                }
            ]
        },
        headers={"X-CSRF-Token": token},
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["applied"] == 0
    assert len(result["conflicts"]) == 1
    assert result["conflicts"][0]["resolution"] == "server_wins"

    # Push revision 2 (should apply)
    response = await client.post(
        f"{SYNC}/push",
        json={
            "events": [
                {
                    "entity_type": "task",
                    "entity_id": entity_id,
                    "action": "update",
                    "revision": 2,
                    "payload": {"title": "v2"},
                }
            ]
        },
        headers={"X-CSRF-Token": token},
    )
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["applied"] == 1
    assert result["conflicts"] == []


async def test_sync_cross_user_denied(client: AsyncClient) -> None:
    alice_client = make_client()
    await register_user(alice_client, email=f"alice-{uuid.uuid4().hex}@example.com")
    await register_device(alice_client, device_id="alice-device")

    bob_client = make_client()
    await register_user(bob_client, email=f"bob-{uuid.uuid4().hex}@example.com")

    # Bob tries to delete Alice's device - should fail (Bob doesn't own it)
    token_bob = await get_csrf(bob_client)
    response = await bob_client.delete(
        f"{SYNC}/devices/alice-device",
        headers={"X-CSRF-Token": token_bob},
    )
    assert response.status_code == 404, response.text


async def test_sync_push_requires_csrf(client: AsyncClient) -> None:
    await register_user(client)
    response = await client.post(f"{SYNC}/push", json={"events": []})
    assert response.status_code == 403, response.text
