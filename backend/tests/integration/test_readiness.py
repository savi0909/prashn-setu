"""The M0 'hello' test: one request that exercises the whole loop.

HTTP → FastAPI → dependency → async engine → asyncpg → migrated Postgres → back.
If this is green in CI, the environment contract holds end to end.
"""

import httpx
import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from app.main import create_app

pytestmark = pytest.mark.integration


async def test_readyz_reports_the_database_is_up(migrated_engine: AsyncEngine) -> None:
    app = create_app()
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/readyz")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "up"}


async def test_openapi_schema_is_generated(migrated_engine: AsyncEngine) -> None:
    """The frontend's generated client (§16.1) is built from this document."""
    app = create_app()
    transport = httpx.ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "Prashn Setu API"
    assert "/healthz" in schema["paths"]
    assert "/readyz" in schema["paths"]
