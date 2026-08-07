"""Liveness and readiness endpoints.

These sit outside ``/api/v1`` on purpose: they are infrastructure contracts for
Docker, Kubernetes and the load balancer, not product API, and they must not
move when the API version does.
"""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.core.logging import get_logger
from app.db.session import get_session

router = APIRouter(tags=["health"])
log = get_logger(__name__)


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    environment: str


class ReadyResponse(BaseModel):
    status: Literal["ready", "degraded"]
    database: Literal["up", "down"]


@router.get("/healthz", response_model=HealthResponse)
async def healthz(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    """Liveness. Deliberately touches no dependency.

    A liveness probe that checks the database will restart a healthy process
    during a database blip, turning a recoverable outage into a crash loop.
    """
    return HealthResponse(
        status="ok",
        service=settings.service_name,
        environment=settings.environment,
    )


@router.get("/readyz", response_model=ReadyResponse)
async def readyz(
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ReadyResponse:
    """Readiness. Takes the instance out of rotation when Postgres is unreachable."""
    try:
        await session.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        # Deliberately broad, and the one place in the codebase where that is
        # correct: every failure means "not ready", and a readiness probe that
        # raises returns 500, which reports a healthy-but-unready instance as a
        # crashing one.
        #
        # Narrowing this to SQLAlchemyError does not work. SQLAlchemy only wraps
        # driver errors once a connection exists and a statement is executing;
        # failures during pool checkout and pre-ping happen below that layer and
        # arrive raw. Observed with Postgres stopped: a builtin ConnectionError
        # ("unexpected connection_lost() call") and asyncpg's
        # CannotConnectNowError ("the database system is starting up") — neither
        # of them a SQLAlchemyError.
        log.warning("readiness_check_failed", error=str(exc), error_type=type(exc).__name__)
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return ReadyResponse(status="degraded", database="down")

    return ReadyResponse(status="ready", database="up")
