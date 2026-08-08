"""SQLAlchemy models, one module per aggregate.

Import every model module here. Alembic's ``env.py`` imports this package to
populate ``Base.metadata``; a model that is not reachable from this file is
invisible to autogenerate and will be silently dropped from migrations.

§5.5 (class_levels, subjects) has landed. §5.6 (examinations, editions,
patterns, syllabus) is next.
"""

from app.db.base import Base
from app.models.reference import ClassLevel, Subject

__all__ = ["Base", "ClassLevel", "Subject"]
