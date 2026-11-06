from httpx import AsyncClient


async def test_unknown_route_returns_problem_details(client: AsyncClient) -> None:
    response = await client.get("/does-not-exist")

    assert response.status_code == 404
    assert response.headers["content-type"] == "application/problem+json"
    payload = response.json()
    assert payload["status"] == 404
    assert payload["code"] == "not_found"
    assert payload["instance"] == "/does-not-exist"
    assert payload["request_id"] == response.headers["x-request-id"]


async def test_request_id_is_echoed_when_valid(client: AsyncClient) -> None:
    request_id = "client-request-1234"
    response = await client.get("/health/live", headers={"X-Request-ID": request_id})

    assert response.headers["x-request-id"] == request_id
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"


async def test_invalid_request_id_is_replaced(client: AsyncClient) -> None:
    response = await client.get("/health/live", headers={"X-Request-ID": "bad id"})

    assert response.headers["x-request-id"] != "bad id"
    assert len(response.headers["x-request-id"]) == 32


async def test_cors_allows_the_configured_web_origin(client: AsyncClient) -> None:
    response = await client.get(
        "/api/v1/meta",
        headers={"Origin": "http://localhost:3000"},
    )

    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert response.headers["access-control-allow-credentials"] == "true"
