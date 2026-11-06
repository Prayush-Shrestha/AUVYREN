from httpx import AsyncClient


async def test_liveness_returns_service_metadata(client: AsyncClient) -> None:
    response = await client.get("/health/live")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "Auvyren API"
    assert payload["version"] == "0.1.0"


async def test_readiness_checks_postgres(client: AsyncClient) -> None:
    response = await client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["database"] == "ok"


async def test_versioned_meta_endpoint(client: AsyncClient) -> None:
    response = await client.get("/api/v1/meta")

    assert response.status_code == 200
    assert response.json() == {
        "name": "Auvyren API",
        "version": "0.1.0",
        "api_version": "v1",
    }


async def test_root_reports_health(client: AsyncClient) -> None:
    response = await client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
