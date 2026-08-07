"""Async engine and session lifecycle.

The engine is a process-level resource created once at start-up and disposed at
shutdown. Sessions are per-request and are never shared across tasks — an
``AsyncSession`` is not concurrency-safe.
"""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import Settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_engine(settings: Settings) -> AsyncEngine:
    """Create the process-wide engine. Called from the app lifespan."""
    global _engine, _session_factory
    if _engine is not None:
        return _engine

    _engine = create_async_engine(
        str(settings.database_url),
        echo=settings.db_echo,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_pre_ping=True,
        # asyncpg caches prepared statements per connection. Behind PgBouncer in
        # transaction mode that cache goes stale and queries fail with
        # "prepared statement does not exist"; disabling it is the standard fix.
        connect_args={"statement_cache_size": 0},
    )
    _session_factory = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    return _engine


async def dispose_engine() -> None:
    """Close every pooled connection. Called from the app lifespan."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None


def get_engine() -> AsyncEngine:
    if _engine is None:
        raise RuntimeError("Engine not initialised; call init_engine() first.")
    return _engine


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency. One session per request, rolled back on any error.

    Commits are the caller's responsibility — a service decides its own
    transaction boundary. This dependency only guarantees the session is closed
    and that an exception never leaves a half-applied transaction on the pool.
    """
    if _session_factory is None:
        raise RuntimeError("Engine not initialised; call init_engine() first.")

    async with _session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
