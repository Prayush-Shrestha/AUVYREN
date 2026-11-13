"""Knowledge workspace tests: note CRUD, search, links, and ownership."""

from __future__ import annotations

import uuid

from app.main import app
from httpx import ASGITransport, AsyncClient

ORIGIN = "http://localhost:3000"
EMAIL_DOMAIN = "phase7.auvyren.app"
PASSWORD = "correct horse battery staple"
KNOWLEDGE = "/api/v1/knowledge"


def unique_email(prefix: str = "knowledge") -> str:
    return f"{prefix}-{uuid.uuid4().hex}@{EMAIL_DOMAIN}"


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


async def auth_headers(client: AsyncClient) -> dict[str, str]:
    return {"X-CSRF-Token": await get_csrf(client)}


async def register(client: AsyncClient, *, email: str | None = None) -> None:
    token = await get_csrf(client)
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email or unique_email(),
            "password": PASSWORD,
            "full_name": "Knowledge Test",
        },
        headers={"X-CSRF-Token": token},
    )
    assert response.status_code == 201, response.text


async def create_note(
    client: AsyncClient,
    headers: dict[str, str],
    *,
    title: str,
    content: str | None = None,
    kind: str = "note",
    tags: str | None = None,
    source_id: str | None = None,
) -> dict:
    payload: dict = {"title": title}
    if content is not None:
        payload["content"] = content
    if kind != "note":
        payload["kind"] = kind
    if tags is not None:
        payload["tags"] = tags
    if source_id is not None:
        payload["source_id"] = source_id
    response = await client.post(KNOWLEDGE, json=payload, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()


async def test_knowledge_requires_authentication(client: AsyncClient) -> None:
    assert (await client.get(KNOWLEDGE)).status_code == 401

    headers = await auth_headers(client)
    for path, body in (
        (KNOWLEDGE, {"title": "Anonymous"}),
        (f"{KNOWLEDGE}/search", {"q": "anything"}),
    ):
        response = await client.post(path, json=body, headers=headers)
        assert response.status_code == 401, f"POST {path}: {response.text}"


async def test_note_crud_round_trip(client: AsyncClient) -> None:
    await register(client)
    headers = await auth_headers(client)

    note = await create_note(
        client,
        headers,
        title="Design language",
        content="Ink, moss, and paper.",
        kind="decision",
        tags="design,identity",
    )
    assert note["title"] == "Design language"
    assert note["kind"] == "decision"
    assert note["source_type"] == "user"
    assert note["deleted_at"] is None

    fetched = await client.get(f"{KNOWLEDGE}/{note['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["content"] == "Ink, moss, and paper."

    updated = await client.patch(
        f"{KNOWLEDGE}/{note['id']}",
        json={"title": "Design language v2", "content": None},
        headers=headers,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["title"] == "Design language v2"
    assert updated.json()["content"] is None

    listed = await client.get(KNOWLEDGE)
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["notes"]] == [note["id"]]


async def test_note_source_id_is_validated_and_round_trips(client: AsyncClient) -> None:
    await register(client)
    headers = await auth_headers(client)
    source_id = uuid.uuid4()

    note = await create_note(
        client,
        headers,
        title="Generated insight",
        source_id=str(source_id),
    )
    assert note["source_id"] == str(source_id)

    invalid = await client.post(
        KNOWLEDGE,
        json={"title": "Bad source", "source_id": "not-a-uuid"},
        headers=headers,
    )
    assert invalid.status_code == 422


async def test_soft_delete_hides_note_and_restore_brings_it_back(
    client: AsyncClient,
) -> None:
    await register(client)
    headers = await auth_headers(client)
    note = await create_note(client, headers, title="Temporary")

    deleted = await client.delete(f"{KNOWLEDGE}/{note['id']}", headers=headers)
    assert deleted.status_code == 204

    hidden = await client.get(f"{KNOWLEDGE}/{note['id']}")
    assert hidden.status_code == 404
    assert hidden.json()["code"] == "note_not_found"

    listed = await client.get(KNOWLEDGE)
    assert listed.json()["notes"] == []

    with_deleted = await client.get(KNOWLEDGE, params={"include_deleted": True})
    assert [item["id"] for item in with_deleted.json()["notes"]] == [note["id"]]

    restored = await client.post(
        f"{KNOWLEDGE}/{note['id']}/restore",
        headers=headers,
    )
    assert restored.status_code == 200, restored.text
    assert restored.json()["deleted_at"] is None

    visible = await client.get(f"{KNOWLEDGE}/{note['id']}")
    assert visible.status_code == 200


async def test_search_matches_title_content_and_tags(client: AsyncClient) -> None:
    await register(client)
    headers = await auth_headers(client)

    await create_note(client, headers, title="Weekly review")
    await create_note(client, headers, title="Meeting", content="Discuss the phi-losophy")
    await create_note(client, headers, title="Ideas", tags="phi-losophy,reading")
    await create_note(client, headers, title="Unrelated")

    search = await client.post(
        f"{KNOWLEDGE}/search",
        json={"q": "phi-losophy"},
        headers=headers,
    )
    assert search.status_code == 200, search.text
    assert search.json()["total"] == 2
    assert {item["title"] for item in search.json()["notes"]} == {"Meeting", "Ideas"}

    filtered = await client.post(
        f"{KNOWLEDGE}/search",
        json={"q": "review", "kind": "journal"},
        headers=headers,
    )
    assert filtered.status_code == 200
    assert filtered.json()["total"] == 0

    no_match = await client.post(
        f"{KNOWLEDGE}/search",
        json={"q": "zzz-not-present"},
        headers=headers,
    )
    assert no_match.status_code == 200
    assert no_match.json() == {"notes": [], "total": 0}


async def test_search_excludes_soft_deleted_notes(client: AsyncClient) -> None:
    await register(client)
    headers = await auth_headers(client)
    note = await create_note(client, headers, title="Ephemeral thought")

    await client.delete(f"{KNOWLEDGE}/{note['id']}", headers=headers)

    search = await client.post(
        f"{KNOWLEDGE}/search",
        json={"q": "Ephemeral"},
        headers=headers,
    )
    assert search.status_code == 200
    assert search.json()["total"] == 0


async def test_list_filters_by_kind_and_paginates(client: AsyncClient) -> None:
    await register(client)
    headers = await auth_headers(client)

    await create_note(client, headers, title="Note one")
    await create_note(client, headers, title="Journal one", kind="journal")
    await create_note(client, headers, title="Note two")

    journals = await client.get(KNOWLEDGE, params={"kind": "journal"})
    assert journals.status_code == 200
    assert [item["title"] for item in journals.json()["notes"]] == ["Journal one"]

    page = await client.get(KNOWLEDGE, params={"limit": 1, "offset": 1})
    assert page.status_code == 200
    assert len(page.json()["notes"]) == 1

    invalid = await client.get(KNOWLEDGE, params={"kind": "not-a-kind"})
    assert invalid.status_code == 422


async def test_notes_are_isolated_between_users(client: AsyncClient) -> None:
    await register(client, email=unique_email("knowledge-owner"))
    headers = await auth_headers(client)
    note = await create_note(client, headers, title="Private owner note")

    async with make_client() as other:
        await register(other, email=unique_email("knowledge-other"))
        other_headers = await auth_headers(other)

        assert (await other.get(KNOWLEDGE)).json()["notes"] == []
        assert (await other.get(f"{KNOWLEDGE}/{note['id']}")).status_code == 404
        assert (
            await other.patch(
                f"{KNOWLEDGE}/{note['id']}",
                json={"title": "Hijacked"},
                headers=other_headers,
            )
        ).status_code == 404
        assert (
            await other.delete(f"{KNOWLEDGE}/{note['id']}", headers=other_headers)
        ).status_code == 404

        search = await other.post(
            f"{KNOWLEDGE}/search",
            json={"q": "Private"},
            headers=other_headers,
        )
        assert search.json()["total"] == 0


async def test_note_links_are_typed_listed_and_deleted(client: AsyncClient) -> None:
    await register(client)
    headers = await auth_headers(client)
    source = await create_note(client, headers, title="Source note")
    target = await create_note(client, headers, title="Target note")

    created = await client.post(
        f"{KNOWLEDGE}/{source['id']}/links",
        json={
            "source_note_id": source["id"],
            "target_note_id": target["id"],
            "link_type": "supports",
        },
        headers=headers,
    )
    assert created.status_code == 201, created.text

    links = await client.get(f"{KNOWLEDGE}/{source['id']}/links")
    assert links.status_code == 200
    assert len(links.json()) == 1
    link = links.json()[0]
    assert link["source_note_id"] == source["id"]
    assert link["target_note_id"] == target["id"]
    assert link["link_type"] == "supports"

    from_target = await client.get(f"{KNOWLEDGE}/{target['id']}/links")
    assert [item["id"] for item in from_target.json()] == [link["id"]]

    deleted = await client.delete(
        f"{KNOWLEDGE}/links/{link['id']}",
        headers=headers,
    )
    assert deleted.status_code == 204
    assert (await client.get(f"{KNOWLEDGE}/{source['id']}/links")).json() == []


async def test_duplicate_link_is_idempotent(client: AsyncClient) -> None:
    await register(client)
    headers = await auth_headers(client)
    source = await create_note(client, headers, title="Source")
    target = await create_note(client, headers, title="Target")
    payload = {
        "source_note_id": source["id"],
        "target_note_id": target["id"],
        "link_type": "relates_to",
    }

    first = await client.post(
        f"{KNOWLEDGE}/{source['id']}/links", json=payload, headers=headers
    )
    second = await client.post(
        f"{KNOWLEDGE}/{source['id']}/links", json=payload, headers=headers
    )
    assert first.status_code == 201 and second.status_code == 201

    links = await client.get(f"{KNOWLEDGE}/{source['id']}/links")
    assert len(links.json()) == 1


async def test_self_link_and_mismatched_source_are_rejected(
    client: AsyncClient,
) -> None:
    await register(client)
    headers = await auth_headers(client)
    note = await create_note(client, headers, title="Self referential")
    other = await create_note(client, headers, title="Another note")

    self_link = await client.post(
        f"{KNOWLEDGE}/{note['id']}/links",
        json={"source_note_id": note["id"], "target_note_id": note["id"]},
        headers=headers,
    )
    assert self_link.status_code == 400
    assert self_link.json()["code"] == "invalid_link"

    mismatch = await client.post(
        f"{KNOWLEDGE}/{other['id']}/links",
        json={"source_note_id": note["id"], "target_note_id": other["id"]},
        headers=headers,
    )
    assert mismatch.status_code == 400
    assert mismatch.json()["code"] == "invalid_link"


async def test_links_cannot_target_another_users_note(client: AsyncClient) -> None:
    await register(client, email=unique_email("link-owner"))
    headers = await auth_headers(client)
    source = await create_note(client, headers, title="Owner source")

    async with make_client() as other:
        await register(other, email=unique_email("link-other"))
        other_headers = await auth_headers(other)
        foreign = await create_note(other, other_headers, title="Foreign note")

        link = await client.post(
            f"{KNOWLEDGE}/{source['id']}/links",
            json={
                "source_note_id": source["id"],
                "target_note_id": foreign["id"],
            },
            headers=headers,
        )
        assert link.status_code == 404
        assert link.json()["code"] == "note_not_found"

        reverse = await other.post(
            f"{KNOWLEDGE}/{foreign['id']}/links",
            json={
                "source_note_id": foreign["id"],
                "target_note_id": source["id"],
            },
            headers=other_headers,
        )
        assert reverse.status_code == 404


async def test_cross_user_link_deletion_is_denied(client: AsyncClient) -> None:
    await register(client, email=unique_email("link-delete-owner"))
    headers = await auth_headers(client)
    source = await create_note(client, headers, title="Owner A")
    target = await create_note(client, headers, title="Owner B")
    created = await client.post(
        f"{KNOWLEDGE}/{source['id']}/links",
        json={"source_note_id": source["id"], "target_note_id": target["id"]},
        headers=headers,
    )
    assert created.status_code == 201
    link_id = (
        await client.get(f"{KNOWLEDGE}/{source['id']}/links")
    ).json()[0]["id"]
    async with make_client() as other:
        await register(other, email=unique_email("link-delete-other"))
        other_headers = await auth_headers(other)
        denied = await other.delete(
            f"{KNOWLEDGE}/links/{link_id}",
            headers=other_headers,
        )
        assert denied.status_code == 404
        assert denied.json()["code"] == "link_not_found"

    still_there = await client.get(f"{KNOWLEDGE}/{source['id']}/links")
    assert len(still_there.json()) == 1


async def test_knowledge_mutations_require_csrf(client: AsyncClient) -> None:
    await register(client)
    response = await client.post(KNOWLEDGE, json={"title": "No CSRF"})
    assert response.status_code == 403
    assert response.json()["code"] == "csrf_validation_failed"
