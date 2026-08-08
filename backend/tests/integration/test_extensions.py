"""Revision 0001 must leave every extension the domain model needs installed."""

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from tests.conftest import BACKEND_DIR

pytestmark = pytest.mark.integration

REQUIRED_EXTENSIONS = {"pgcrypto", "citext", "ltree", "vector"}


async def test_required_extensions_are_installed(migrated_engine: AsyncEngine) -> None:
    async with migrated_engine.connect() as connection:
        result = await connection.execute(text("SELECT extname FROM pg_extension"))
        installed = {row[0] for row in result}

    assert REQUIRED_EXTENSIONS.issubset(installed), f"missing: {REQUIRED_EXTENSIONS - installed}"


async def test_ltree_containment_operator_works(migrated_engine: AsyncEngine) -> None:
    """The predicate §5.6 relies on for subtree queries on syllabus_nodes."""
    async with migrated_engine.connect() as connection:
        result = await connection.execute(
            text(
                "SELECT 'physics.mechanics.rotational_motion'::ltree <@ 'physics.mechanics'::ltree"
            )
        )
        assert result.scalar_one() is True


async def test_gen_random_uuid_is_available(migrated_engine: AsyncEngine) -> None:
    """Every primary key in §5 defaults to this."""
    async with migrated_engine.connect() as connection:
        result = await connection.execute(text("SELECT gen_random_uuid()"))
        assert result.scalar_one() is not None


async def test_citext_compares_case_insensitively(migrated_engine: AsyncEngine) -> None:
    """§5.3 stores admin_email and users.email as CITEXT."""
    async with migrated_engine.connect() as connection:
        result = await connection.execute(
            text("SELECT 'Teacher@School.IN'::citext = 'teacher@school.in'::citext")
        )
        assert result.scalar_one() is True


async def test_migrations_are_reversible(migrated_engine: AsyncEngine) -> None:
    """§16.2: a revision is reversible or documented as irreversible.

    Asserts the alembic_version table exists at head — the downgrade path itself
    is exercised by the ``make migrate-check`` target in CI, which round-trips
    ``downgrade base`` and ``upgrade head`` against a scratch database.

    Head is read from the script directory rather than hard-coded. A literal
    here has to be edited by every migration that lands, which makes it a
    tripwire for the author rather than a check on the schema.
    """
    alembic_cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    head = ScriptDirectory.from_config(alembic_cfg).get_current_head()

    async with migrated_engine.connect() as connection:
        result = await connection.execute(text("SELECT version_num FROM alembic_version"))
        assert result.scalar_one() == head
