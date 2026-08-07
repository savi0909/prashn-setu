"""Enable required PostgreSQL extensions

Revision ID: 0001
Revises:
Create Date: 2026-08-07

Every extension the domain model depends on, enabled before any table exists:

- ``pgcrypto``  — ``gen_random_uuid()`` for primary keys (§5.1). Postgres 13+
  provides ``gen_random_uuid()`` in core, but §5.1 names pgcrypto and the rest
  of it (``digest``, ``crypt``) is wanted for token hashing in §5.16.
- ``citext``    — case-insensitive email columns (§5.3 ``organizations.admin_email``,
  ``users.email``).
- ``ltree``     — materialised path on ``syllabus_nodes.path`` (§5.6). This is what
  makes ``WHERE path <@ 'physics.mechanics'`` a single indexed predicate.
- ``vector``    — pgvector embeddings for duplicate detection (§5.10,
  ``question_embeddings``).
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

EXTENSIONS = ("pgcrypto", "citext", "ltree", "vector")


def upgrade() -> None:
    for ext in EXTENSIONS:
        op.execute(f'CREATE EXTENSION IF NOT EXISTS "{ext}"')


def downgrade() -> None:
    # Reverse order: nothing here depends on anything else here, but keeping the
    # symmetry makes the pattern obvious once dependent extensions appear.
    for ext in reversed(EXTENSIONS):
        op.execute(f'DROP EXTENSION IF EXISTS "{ext}"')
