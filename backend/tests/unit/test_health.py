"""Liveness and readiness endpoints. No database, no container, no network."""

import httpx
import pytest

from app.db.session import get_session
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


@pytest.mark.parametrize(
    "failure",
    [
        # Both observed live with Postgres stopped. Neither is a SQLAlchemyError:
        # they are raised during pool checkout and pre-ping, below the layer where
        # SQLAlchemy wraps driver errors.
        ConnectionError("unexpected connection_lost() call"),
        RuntimeError("the database system is starting up"),
    ],
    ids=["builtin-connection-error", "raw-driver-error"],
)
async def test_readyz_degrades_instead_of_raising(failure: Exception) -> None:
    """Regression: readyz must return 503, never 500.

    A 503 tells the load balancer "not ready, stop routing here". A 500 reports
    a healthy-but-unready instance as a crashing one, which is a different
    incident with a different response.
    """
    app = create_app()

    class _DeadSession:
        async def execute(self, *_args: object) -> None:
            raise failure

    app.dependency_overrides[get_session] = _DeadSession

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as http_client:
        response = await http_client.get("/readyz")

    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "database": "down"}
