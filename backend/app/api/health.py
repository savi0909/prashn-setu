"""Liveness and readiness endpoints.

These sit outside ``/api/v1`` on purpose: they are infrastructure contracts for
Docker, Kubernetes and the load balancer, not product API, and they must not
move when the API version does.
"""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
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
    except SQLAlchemyError as exc:
        log.warning("readiness_check_failed", error=str(exc))
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return ReadyResponse(status="degraded", database="down")

    return ReadyResponse(status="ready", database="up")
