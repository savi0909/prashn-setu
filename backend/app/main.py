"""FastAPI application factory and process lifespan."""

import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, Response

from app.api.health import router as health_router
from app.config import Settings, get_settings
from app.core.logging import configure_logging, get_logger
from app.db.session import dispose_engine, init_engine

log = get_logger(__name__)

REQUEST_ID_HEADER = "X-Request-ID"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings: Settings = get_settings()
    configure_logging(settings)
    init_engine(settings)
    log.info("startup", environment=settings.environment, service=settings.service_name)
    try:
        yield
    finally:
        await dispose_engine()
        log.info("shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings)

    app = FastAPI(
        title="Prashn Setu API",
        version="0.1.0",
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url=None,
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    @app.middleware("http")
    async def request_context(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Bind a request id into the logging context for the whole request.

        structlog's contextvars survive across ``await`` boundaries, so every
        log line emitted downstream — including from services and repositories
        that know nothing about HTTP — carries the same id without threading a
        logger through call signatures.
        """
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response

    app.include_router(health_router)

    return app


app = create_app()
