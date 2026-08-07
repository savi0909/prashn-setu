"""Structured logging.

One configuration call at start-up. Every log line carries the same keys, so
the same query works in `docker compose logs` locally and in Loki in production
(§15.3). Console renderer locally for readability, JSON everywhere else.

Logs from libraries that use the stdlib logger — uvicorn, sqlalchemy, alembic —
are rendered by the same formatter as our own structlog calls. Without that,
half the output is structured and half is not, which defeats the point: you
cannot filter an access log by ``request_id`` if the access log is a bare
string.
"""

import logging
import sys

import structlog

from app.config import Settings

# Loggers that install their own handlers at import time. Left alone, uvicorn
# emits through its own formatter and bypasses everything configured here.
_HIJACKED_LOGGERS = (
    "uvicorn",
    "uvicorn.error",
    "uvicorn.access",
    "sqlalchemy.engine",
    "alembic",
)


def configure_logging(settings: Settings) -> None:
    """Idempotent. Safe to call from the app lifespan and from a Celery worker."""
    level = getattr(logging, settings.log_level)

    # Applied to structlog events and to stdlib records alike, so both carry the
    # same keys before the renderer sees them.
    shared_processors: list[structlog.typing.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    structlog.configure(
        processors=[
            *shared_processors,
            # Hands the event dict to the stdlib formatter below rather than
            # rendering here; that is what lets both sources share a renderer.
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    renderer: structlog.typing.Processor = (
        structlog.processors.JSONRenderer()
        if settings.log_json
        else structlog.dev.ConsoleRenderer(colors=False)
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        # Records from stdlib loggers never went through structlog's processor
        # chain, so they get it here.
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    for name in _HIJACKED_LOGGERS:
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = True

    # SQL echo is controlled by Settings.db_echo, not by the root level.
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.db_echo else logging.WARNING
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    logger: structlog.stdlib.BoundLogger = structlog.get_logger(name)
    return logger
