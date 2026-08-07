"""Typed application settings.

Every environment variable the backend reads is declared here (§16.3). Nothing
else in the codebase may call ``os.environ`` — if a value comes from the
environment, it gets a field on this model so it is typed, validated at start-up,
and discoverable in one place.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["local", "test", "staging", "production"]

# Appendix E puts .env at the repository root. Resolving it from this module's
# location rather than the cwd means `make dev` (cwd=backend), `pytest`
# (cwd=backend) and `docker compose` (cwd=root) all read the same file.
REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="forbid",
    )

    environment: Environment = "local"
    debug: bool = False

    # --- service identity -------------------------------------------------
    service_name: str = "prashn-setu-backend"
    api_v1_prefix: str = "/api/v1"

    # --- database ---------------------------------------------------------
    database_url: PostgresDsn = Field(
        default=PostgresDsn("postgresql+asyncpg://prashn:prashn@localhost:55432/prashn_setu"),
        description=(
            "Async SQLAlchemy DSN. Must use the asyncpg driver. Port 55432, not 5432 — "
            "see the note at the top of docker-compose.yml."
        ),
    )
    db_pool_size: int = 10
    db_max_overflow: int = 5
    db_echo: bool = False

    # --- logging ----------------------------------------------------------
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_json: bool = Field(
        default=False,
        description="JSON lines for log shipping. Off locally, on everywhere else.",
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def alembic_url(self) -> str:
        """Alembic runs its own engine; it needs the DSN as a plain string."""
        return str(self.database_url)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached accessor. FastAPI dependencies and Celery tasks both use this."""
    return Settings()
