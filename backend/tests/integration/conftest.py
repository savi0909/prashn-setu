"""A real Postgres 16 + pgvector, migrated to head, for the whole session.

Set ``TEST_DATABASE_URL`` to point at an already-running database and the
container is skipped — useful for a fast local edit/run loop. CI leaves it unset
so every run starts from an empty volume and proves the migrations apply from
scratch.
"""

import asyncio
import os
import time
from collections.abc import Iterator

import asyncpg
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import AsyncEngine
from testcontainers.core.container import DockerContainer

from app.config import get_settings
from app.db.session import dispose_engine, init_engine
from tests.conftest import BACKEND_DIR

POSTGRES_IMAGE = "pgvector/pgvector:pg16"
STARTUP_TIMEOUT_SECONDS = 90


def _wait_until_accepting_connections(dsn: str, timeout: int = STARTUP_TIMEOUT_SECONDS) -> None:
    """Poll with a real connection.

    The postgres image logs "ready to accept connections" once during initdb —
    while still refusing external connections — and again for real. Log-scraping
    therefore races; connecting does not.
    """

    async def probe() -> None:
        deadline = time.monotonic() + timeout
        last_error: Exception | None = None
        while time.monotonic() < deadline:
            try:
                connection = await asyncpg.connect(dsn)
            except (OSError, asyncpg.PostgresError) as exc:
                last_error = exc
                await asyncio.sleep(0.5)
            else:
                await connection.close()
                return
        raise TimeoutError(f"Postgres not ready within {timeout}s: {last_error}")

    asyncio.run(probe())


@pytest.fixture(scope="session")
def postgres_dsn() -> Iterator[str]:
    """asyncpg-flavoured DSN for a migrated, empty database."""
    external = os.environ.get("TEST_DATABASE_URL")
    if external:
        _wait_until_accepting_connections(external.replace("+asyncpg", ""))
        yield external
        return

    container = (
        DockerContainer(POSTGRES_IMAGE)
        .with_env("POSTGRES_USER", "test")
        .with_env("POSTGRES_PASSWORD", "test")
        .with_env("POSTGRES_DB", "test")
        .with_exposed_ports(5432)
    )
    container.start()
    try:
        host = container.get_container_host_ip()
        port = container.get_exposed_port(5432)
        _wait_until_accepting_connections(f"postgresql://test:test@{host}:{port}/test")
        yield f"postgresql+asyncpg://test:test@{host}:{port}/test"
    finally:
        container.stop()


@pytest.fixture(scope="session")
def migrated_engine(postgres_dsn: str) -> Iterator[AsyncEngine]:
    """Run ``alembic upgrade head``, then hand back an initialised engine."""
    os.environ["DATABASE_URL"] = postgres_dsn
    get_settings.cache_clear()

    alembic_cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    command.upgrade(alembic_cfg, "head")

    engine = init_engine(get_settings())
    try:
        yield engine
    finally:
        asyncio.run(dispose_engine())
        get_settings.cache_clear()
