"""Declarative base for all ORM models.

Every model in ``app/models/`` inherits from ``Base``. Alembic's autogenerate
reads ``Base.metadata``, so a model that is not imported before autogenerate runs
will not appear in the migration — ``app/models/__init__.py`` exists to import
them all in one place.
"""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Explicit constraint naming. Without this, Postgres auto-generates names for
# indexes and constraints, and Alembic cannot write a reversible downgrade
# because it does not know what to drop. §16.2 requires reversible revisions.
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
