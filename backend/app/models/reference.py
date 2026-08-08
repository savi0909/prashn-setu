"""Reference data: the grade axis and the subject taxonomy (§5.5 subset).

Only `class_levels` and `subjects` land here. §5.5's other two tables,
`teacher_profiles` and `teacher_assignments`, carry `organization_id` and
reference `users`, so they wait for M1 — see ADR 0001, which scopes §5.5 to
"class_levels and subjects only".

Constraints are declared on the model *and* written into migration 0002. The
knowledge base already validates all of this at parse time (`app/seeds/kb.py`),
but an admin UI arrives at M4 (§15.4) and the seed loader stops being the only
writer.
"""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    Text,
    func,
    text,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

# The stream vocabulary is small and stable, so §5.1 calls for a CHECK rather
# than a native enum — a new stream should be a one-line migration, not a
# type alteration.
STREAMS = ("SCIENCE", "COMMERCE", "ARTS")

# Screaming snake case. Enforced here as well as in the knowledge base because
# a lower-cased near-miss of an existing code is indistinguishable from a new
# subject, and questions anchor to codes (RULE subj-004).
SUBJECT_CODE_PATTERN = "^[A-Z][A-Z0-9_]*$"


class ClassLevel(Base):
    """One school grade, keyed by the grade integer itself (§5.5)."""

    __tablename__ = "class_levels"

    # autoincrement=False: 9 means Class 9. A surrogate key here would make
    # every URL and every foreign key one join away from being readable.
    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=False)
    name_en: Mapped[str] = mapped_column(Text, nullable=False)
    name_hi: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (CheckConstraint("id BETWEEN 1 AND 12", name="id_range"),)


class Subject(Base):
    """One subject in the taxonomy (document 2, Appendix C)."""

    __tablename__ = "subjects"

    id: Mapped[UUID] = mapped_column(
        postgresql.UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    code: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    name_en: Mapped[str] = mapped_column(Text, nullable=False)
    name_hi: Mapped[str] = mapped_column(Text, nullable=False)
    stream: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Competitive-only subjects exist so competitive papers can be structured
    # but are taught in no grade, so they are hidden from the assignment picker
    # (§7.4). Appendix C named this flag; the §5.5 DDL never declared it.
    is_teachable: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))

    # Appendix C's class ranges are all contiguous, so two bounds express them
    # exactly and `GET /ref/subjects?class_level=9` is a BETWEEN with no join.
    min_class_level: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    max_class_level: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)

    # Appendix C's NSQF_VOCATIONAL is "a parent node; trades as children", and
    # document 2 §4.8 puts BOTANY and ZOOLOGY under BIOLOGY. Nullable, and at
    # most one level deep — enforced by RULE subj-005 rather than by the
    # database, since a recursive CHECK is not expressible.
    parent_subject_id: Mapped[UUID | None] = mapped_column(
        postgresql.UUID(as_uuid=True), ForeignKey("subjects.id"), nullable=True
    )

    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1000"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "stream IN ('SCIENCE', 'COMMERCE', 'ARTS')",
            name="stream",
        ),
        CheckConstraint(f"code ~ '{SUBJECT_CODE_PATTERN}'", name="code_format"),
        # Both bounds or neither. One bound alone reads as an open interval
        # nobody wrote down.
        CheckConstraint(
            "(min_class_level IS NULL) = (max_class_level IS NULL)",
            name="class_pair",
        ),
        CheckConstraint("min_class_level <= max_class_level", name="class_order"),
        CheckConstraint(
            "min_class_level BETWEEN 1 AND 12 AND max_class_level BETWEEN 1 AND 12",
            name="class_bounds",
        ),
        # §16.2: every foreign key has an index unless there is a written
        # reason. Reading a parent's children is how §7.4 renders the picker.
        Index("ix_subjects_parent_subject_id", "parent_subject_id"),
    )
