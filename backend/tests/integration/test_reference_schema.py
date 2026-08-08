"""Migration 0002 — the constraints, not just the columns.

Appendix C describes rules the §5.5 DDL never implemented. The knowledge base
enforces them at parse time, but the database is the last line: an admin UI
lands at M4 (§15.4) and the seed loader stops being the only writer. Each test
here proves a constraint actually rejects bad data rather than merely existing.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

pytestmark = pytest.mark.integration

INSERT_SUBJECT = text(
    """
    INSERT INTO subjects (code, name_en, name_hi, stream, is_teachable,
                          min_class_level, max_class_level, parent_subject_id, sort_order)
    VALUES (:code, :name_en, :name_hi, :stream, :is_teachable,
            :min_class_level, :max_class_level, :parent_subject_id, :sort_order)
    """
)


def _subject(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "code": "TEST_SUBJECT",
        "name_en": "Test Subject",
        "name_hi": "परीक्षण विषय",
        "stream": None,
        "is_teachable": True,
        "min_class_level": 6,
        "max_class_level": 10,
        "parent_subject_id": None,
        "sort_order": 9000,
    }
    return base | overrides


# ------------------------------------------------------------- class_levels


@pytest.mark.parametrize("bad_id", [0, 13])
async def test_class_levels_rejects_an_id_outside_one_to_twelve(
    migrated_engine: AsyncEngine, bad_id: int
) -> None:
    """The DDL comment said `-- 1..12`; a comment enforces nothing."""
    async with migrated_engine.connect() as connection:
        with pytest.raises(IntegrityError):
            await connection.execute(
                text("INSERT INTO class_levels (id, name_en, name_hi) VALUES (:id, 'x', 'x')"),
                {"id": bad_id},
            )


async def test_class_levels_holds_every_grade_after_seeding(migrated_engine: AsyncEngine) -> None:
    """Migration 0002 creates the table empty; the seed loader fills it.

    Asserted as "no rows outside 1-12" rather than "twelve rows", so the test
    describes the constraint rather than the seed state.
    """
    async with migrated_engine.connect() as connection:
        result = await connection.execute(
            text("SELECT count(*) FROM class_levels WHERE id NOT BETWEEN 1 AND 12")
        )
        assert result.scalar_one() == 0


# ------------------------------------------------------------------ subjects


async def test_subjects_rejects_an_unknown_stream(migrated_engine: AsyncEngine) -> None:
    """§5.1: stable vocabularies get a CHECK. HUMANITIES is not in it."""
    async with migrated_engine.connect() as connection:
        with pytest.raises(IntegrityError):
            await connection.execute(INSERT_SUBJECT, _subject(stream="HUMANITIES"))


async def test_subjects_rejects_a_half_specified_class_range(migrated_engine: AsyncEngine) -> None:
    async with migrated_engine.connect() as connection:
        with pytest.raises(IntegrityError):
            await connection.execute(INSERT_SUBJECT, _subject(max_class_level=None))


async def test_subjects_rejects_an_inverted_class_range(migrated_engine: AsyncEngine) -> None:
    async with migrated_engine.connect() as connection:
        with pytest.raises(IntegrityError):
            await connection.execute(
                INSERT_SUBJECT, _subject(min_class_level=10, max_class_level=6)
            )


async def test_subjects_rejects_a_class_level_outside_one_to_twelve(
    migrated_engine: AsyncEngine,
) -> None:
    async with migrated_engine.connect() as connection:
        with pytest.raises(IntegrityError):
            await connection.execute(
                INSERT_SUBJECT, _subject(min_class_level=1, max_class_level=13)
            )


async def test_subjects_rejects_a_malformed_code(migrated_engine: AsyncEngine) -> None:
    """Codes are anchors (RULE subj-004); a lower-cased near-miss must not exist."""
    async with migrated_engine.connect() as connection:
        with pytest.raises(IntegrityError):
            await connection.execute(INSERT_SUBJECT, _subject(code="social-science"))


async def test_subjects_code_is_unique(migrated_engine: AsyncEngine) -> None:
    async with migrated_engine.connect() as connection:
        await connection.execute(INSERT_SUBJECT, _subject(code="TEST_DUPLICATE"))
        with pytest.raises(IntegrityError):
            await connection.execute(INSERT_SUBJECT, _subject(code="TEST_DUPLICATE"))


async def test_subject_parent_must_reference_an_existing_subject(
    migrated_engine: AsyncEngine,
) -> None:
    async with migrated_engine.connect() as connection:
        with pytest.raises(IntegrityError):
            await connection.execute(
                INSERT_SUBJECT,
                _subject(parent_subject_id="00000000-0000-0000-0000-000000000000"),
            )


# ------------------------------------------------------------- updated_at


async def test_updated_at_advances_when_a_subject_changes(migrated_engine: AsyncEngine) -> None:
    """Postgres has no ON UPDATE, so a trigger does it.

    Without this, §6.3's ETags on /ref/subjects go stale the first time anyone
    writes through the ORM, and every client caches a wrong catalogue for an
    hour. Deliberately spans separate transactions: ``now()`` is transaction
    start time, so an insert and update in one transaction share a timestamp
    and the test would pass whether or not the trigger exists.
    """
    code = "TEST_TRIGGER"
    try:
        async with migrated_engine.begin() as connection:
            await connection.execute(INSERT_SUBJECT, _subject(code=code))

        async with migrated_engine.begin() as connection:
            before = await connection.scalar(
                text("SELECT updated_at FROM subjects WHERE code = :code"), {"code": code}
            )

        async with migrated_engine.begin() as connection:
            await connection.execute(
                text("UPDATE subjects SET name_en = 'Renamed' WHERE code = :code"), {"code": code}
            )

        async with migrated_engine.begin() as connection:
            after = await connection.scalar(
                text("SELECT updated_at FROM subjects WHERE code = :code"), {"code": code}
            )

        assert after > before
    finally:
        async with migrated_engine.begin() as connection:
            await connection.execute(
                text("DELETE FROM subjects WHERE code = :code"), {"code": code}
            )
