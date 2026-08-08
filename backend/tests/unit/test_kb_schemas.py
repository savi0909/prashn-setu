"""Schema contract for the domain knowledge base.

``shared/domain/`` is master for the subject taxonomy and the class-level list
(ADR 0002). Nothing hand-maintains a second copy and no reviewer reads 45 rows
of YAML carefully, so this schema is the only thing standing between a typo and
a bad seed run.
"""

import pytest
from pydantic import ValidationError

from app.seeds.kb import ClassLevel, Subject

# ------------------------------------------------------------------ subjects


def test_subject_parses_a_minimal_record() -> None:
    subject = Subject.model_validate(
        {"code": "PHYSICS", "name_en": "Physics", "name_hi": "भौतिक विज्ञान"}
    )

    assert subject.code == "PHYSICS"
    assert subject.stream is None
    # Most subjects are taught in schools; only the competitive-exam-only ones
    # opt out, so TRUE is the default that keeps the YAML quiet.
    assert subject.is_teachable is True


def test_subject_rejects_an_unknown_key() -> None:
    """``extra='forbid'``: a misspelt key must fail loudly, not be dropped.

    Without this, ``strem: SCIENCE`` seeds a subject with no stream and nothing
    anywhere reports it.
    """
    with pytest.raises(ValidationError):
        Subject.model_validate(
            {
                "code": "PHYSICS",
                "name_en": "Physics",
                "name_hi": "भौतिक विज्ञान",
                "strem": "SCIENCE",
            }
        )


def test_subject_requires_a_hindi_name() -> None:
    """§5.5 makes ``name_hi`` NOT NULL — the product is bilingual by default."""
    with pytest.raises(ValidationError):
        Subject.model_validate({"code": "PHYSICS", "name_en": "Physics"})


# -------------------------------------------------------------- class levels


def test_class_level_parses_a_minimal_record() -> None:
    class_level = ClassLevel.model_validate({"id": 9, "name_en": "Class 9", "name_hi": "कक्षा 9"})

    assert class_level.id == 9
    assert class_level.name_hi == "कक्षा 9"


def test_class_level_rejects_an_unknown_key() -> None:
    with pytest.raises(ValidationError):
        ClassLevel.model_validate({"id": 9, "name_en": "Class 9", "name_hi": "कक्षा 9", "grade": 9})


@pytest.mark.parametrize("bad_id", [0, 13, -1])
def test_class_level_rejects_an_id_outside_one_to_twelve(bad_id: int) -> None:
    """Indian schooling runs 1-12. There is no Class 0 and no Class 13."""
    with pytest.raises(ValidationError):
        ClassLevel.model_validate({"id": bad_id, "name_en": "x", "name_hi": "x"})


# --------------------------------------------------------------- class ranges


def _subject(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {"code": "SCIENCE", "name_en": "Science", "name_hi": "विज्ञान"}
    return base | overrides


def test_subject_accepts_a_contiguous_class_range() -> None:
    """Appendix C's ranges are all contiguous, so two bounds express them exactly."""
    subject = Subject.model_validate(_subject(min_class_level=6, max_class_level=10))

    assert subject.min_class_level == 6
    assert subject.max_class_level == 10


def test_subject_rejects_a_half_specified_class_range() -> None:
    """Both bounds or neither. One bound alone has no defensible meaning."""
    with pytest.raises(ValidationError):
        Subject.model_validate(_subject(min_class_level=6))


def test_subject_rejects_an_inverted_class_range() -> None:
    with pytest.raises(ValidationError):
        Subject.model_validate(_subject(min_class_level=10, max_class_level=6))


@pytest.mark.parametrize(
    ("low", "high"),
    [(0, 10), (6, 13)],
)
def test_subject_rejects_a_class_range_outside_one_to_twelve(low: int, high: int) -> None:
    with pytest.raises(ValidationError):
        Subject.model_validate(_subject(min_class_level=low, max_class_level=high))


# --------------------------------------------------------- stream, code, parent


def test_subject_rejects_an_unknown_stream() -> None:
    """§5.5's stream vocabulary is SCIENCE | COMMERCE | ARTS. 'HUMANITIES' is not it."""
    with pytest.raises(ValidationError):
        Subject.model_validate(_subject(stream="HUMANITIES"))


@pytest.mark.parametrize("bad_code", ["physics", "Physics", "SOCIAL-SCIENCE", "2_WHEELER", ""])
def test_subject_rejects_a_code_that_is_not_screaming_snake_case(bad_code: str) -> None:
    """Codes are stable identifiers that questions anchor to (Appendix C).

    Constraining the shape now is what makes ``RULE subj-004`` — codes never
    change — enforceable rather than aspirational.
    """
    with pytest.raises(ValidationError):
        Subject.model_validate(_subject(code=bad_code))


def test_subject_accepts_a_parent_code() -> None:
    """Appendix C annotates NSQF_VOCATIONAL as a parent node with trades beneath it.

    The knowledge base names the parent by code; the loader resolves it to
    ``parent_subject_id`` once both rows exist.
    """
    subject = Subject.model_validate(
        _subject(code="CROP_PRODUCTION", parent="NSQF_VOCATIONAL", is_teachable=False)
    )

    assert subject.parent == "NSQF_VOCATIONAL"


def test_subject_defaults_to_no_parent() -> None:
    assert Subject.model_validate(_subject()).parent is None


def test_subject_carries_a_sort_order_with_a_default() -> None:
    """§5.5 gives `sort_order` a default of 1000 so unordered subjects sink.

    The picker in §7.4 is subject-first, so ordering is a product concern, not a
    cosmetic one — languages before sciences before competitive-only.
    """
    assert Subject.model_validate(_subject()).sort_order == 1000
    assert Subject.model_validate(_subject(sort_order=100)).sort_order == 100
