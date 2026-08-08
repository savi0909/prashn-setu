"""Class levels and subjects — the §5.5 subset

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-08

The sole upstream dependency of §5.6, and the first tables in the corpus-first
order (ADR 0001). §5.5's other two tables wait for M1: `teacher_profiles` and
`teacher_assignments` both carry `organization_id` and reference `users`.

Three columns here are not in the §5.5 DDL. Each closes a gap between what
Appendix C states in prose and what the schema implements — see ADR 0002:

- ``is_teachable``  — Appendix C hides competitive-only subjects from the
  teacher-assignment picker via this flag; the DDL never declared it.
- ``min_class_level`` / ``max_class_level`` — Appendix C gives every taught
  subject a class range and §6.3 ships ``GET /ref/subjects?class_level=``,
  which had nothing to filter on.
- ``parent_subject_id`` — Appendix C annotates NSQF_VOCATIONAL as a parent
  node with trades as children, and document 2 §4.8 puts BOTANY and ZOOLOGY
  under BIOLOGY.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Postgres has no ON UPDATE clause, so `updated_at` needs a trigger. One shared
# function, created here, attached to every table that carries the column from
# now on. Without it the ETags in §6.3 go stale the first time anyone writes
# through the ORM and every client caches a wrong catalogue for an hour.
#
# `now()` is transaction start time, which is what we want: two rows changed in
# one transaction should share a modification timestamp.
SET_UPDATED_AT = """
CREATE OR REPLACE FUNCTION set_updated_at() RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql
"""

TABLES_WITH_UPDATED_AT = ("class_levels", "subjects")


def _attach_updated_at_trigger(table: str) -> None:
    op.execute(
        f"CREATE TRIGGER trg_{table}_set_updated_at "
        f"BEFORE UPDATE ON {table} "
        f"FOR EACH ROW EXECUTE FUNCTION set_updated_at()"
    )


def upgrade() -> None:
    op.execute(SET_UPDATED_AT)

    op.create_table(
        "class_levels",
        # Not autoincrementing: 9 means Class 9. A surrogate here would put a
        # join between every URL and a readable grade.
        sa.Column("id", sa.SmallInteger(), autoincrement=False, nullable=False),
        sa.Column("name_en", sa.Text(), nullable=False),
        sa.Column("name_hi", sa.Text(), nullable=False),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name="pk_class_levels"),
        sa.CheckConstraint("id BETWEEN 1 AND 12", name="ck_class_levels_id_range"),
    )

    op.create_table(
        "subjects",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("name_en", sa.Text(), nullable=False),
        sa.Column("name_hi", sa.Text(), nullable=False),
        sa.Column("stream", sa.Text(), nullable=True),
        sa.Column("is_teachable", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("min_class_level", sa.SmallInteger(), nullable=True),
        sa.Column("max_class_level", sa.SmallInteger(), nullable=True),
        sa.Column("parent_subject_id", sa.UUID(), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default=sa.text("1000"), nullable=False),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name="pk_subjects"),
        sa.UniqueConstraint("code", name="uq_subjects_code"),
        sa.ForeignKeyConstraint(
            ["parent_subject_id"], ["subjects.id"], name="fk_subjects_parent_subject_id_subjects"
        ),
        # §5.1: a small stable vocabulary gets a CHECK rather than a native
        # enum, so adding a stream is a one-line migration.
        sa.CheckConstraint("stream IN ('SCIENCE', 'COMMERCE', 'ARTS')", name="ck_subjects_stream"),
        # A lower-cased near-miss of an existing code is indistinguishable from
        # a new subject, and questions anchor to codes (RULE subj-004).
        sa.CheckConstraint("code ~ '^[A-Z][A-Z0-9_]*$'", name="ck_subjects_code_format"),
        sa.CheckConstraint(
            "(min_class_level IS NULL) = (max_class_level IS NULL)", name="ck_subjects_class_pair"
        ),
        sa.CheckConstraint("min_class_level <= max_class_level", name="ck_subjects_class_order"),
        sa.CheckConstraint(
            "min_class_level BETWEEN 1 AND 12 AND max_class_level BETWEEN 1 AND 12",
            name="ck_subjects_class_bounds",
        ),
    )
    # §16.2: every foreign key gets an index. Reading a parent's children is
    # how the §7.4 picker renders its one level of nesting.
    op.create_index("ix_subjects_parent_subject_id", "subjects", ["parent_subject_id"])

    for table in TABLES_WITH_UPDATED_AT:
        _attach_updated_at_trigger(table)


def downgrade() -> None:
    # Triggers go with their tables; the function outlives neither, so it is
    # dropped last and explicitly.
    op.drop_index("ix_subjects_parent_subject_id", table_name="subjects")
    op.drop_table("subjects")
    op.drop_table("class_levels")
    op.execute("DROP FUNCTION IF EXISTS set_updated_at()")
