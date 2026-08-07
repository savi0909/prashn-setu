"""Liveness endpoint. No database, no container, no network."""

import httpx
import pytest

from app.main import create_app


@pytest.fixture
def client() -> httpx.AsyncClient:
    # No LifespanManager: create_app() builds the routes without opening the
    # engine, which is exactly the property /healthz is supposed to have.
    app = create_app()
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


async def test_healthz_reports_ok_without_a_database(client: httpx.AsyncClient) -> None:
    async with client:
        response = await client.get("/healthz")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "prashn-setu-backend"


async def test_healthz_echoes_a_request_id(client: httpx.AsyncClient) -> None:
    async with client:
        response = await client.get("/healthz", headers={"X-Request-ID": "abc-123"})

    assert response.headers["X-Request-ID"] == "abc-123"


async def test_healthz_generates_a_request_id_when_absent(client: httpx.AsyncClient) -> None:
    async with client:
        response = await client.get("/healthz")

    assert response.headers.get("X-Request-ID")
