"""SQLAlchemy models, one module per aggregate.

Import every model module here. Alembic's ``env.py`` imports this package to
populate ``Base.metadata``; a model that is not reachable from this file is
invisible to autogenerate and will be silently dropped from migrations.

Empty at M0. §5.5 (class_levels, subjects) and §5.6 (examinations, editions,
blueprints, syllabus) land next.
"""

from app.db.base import Base

__all__ = ["Base"]
