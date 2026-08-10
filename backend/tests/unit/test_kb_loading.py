"""The knowledge base on disk must parse, and parse into what we expect.

These read the real ``shared/domain/`` files rather than fixtures. That is the
point: the files *are* the master copy (ADR 0002), so a test against a fixture
would prove nothing about what the seed loader will actually write.
"""

import pytest

from app.seeds.kb import load_knowledge_base


def test_knowledge_base_parses() -> None:
    """Every file validates against its schema. The whole contract, in one line."""
    knowledge_base = load_knowledge_base()

    assert knowledge_base.subjects
    assert knowledge_base.class_levels


def test_every_class_level_from_one_to_twelve_is_present() -> None:
    """§5.5 keys `class_levels` by the grade integer; gaps would break FK targets."""
    ids = sorted(level.id for level in load_knowledge_base().class_levels)

    assert ids == list(range(1, 13))


def test_subject_codes_are_unique() -> None:
    """`subjects.code` is UNIQUE in §5.5, so a duplicate fails at seed time.

    Catching it here means the failure names the offending code instead of
    surfacing as an opaque integrity error three layers down.
    """
    codes = [subject.code for subject in load_knowledge_base().subjects]
    duplicated = sorted({code for code in codes if codes.count(code) > 1})

    assert not duplicated, f"duplicated subject codes: {duplicated}"


def test_subject_lookup_by_code_finds_a_known_subject() -> None:
    knowledge_base = load_knowledge_base()

    assert knowledge_base.subject_by_code("PHYSICS").name_en == "Physics"


def test_subject_lookup_by_code_raises_for_an_unknown_subject() -> None:
    with pytest.raises(KeyError):
        load_knowledge_base().subject_by_code("ASTROLOGY")
