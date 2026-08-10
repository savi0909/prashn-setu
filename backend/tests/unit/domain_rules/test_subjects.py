"""Rules the subject taxonomy must satisfy, as tests rather than prose.

Each of these was a sentence in Appendix C or document 2 §4.8 that the §5.5 DDL
did not implement. Prose the schema does not enforce is indistinguishable from
prose it does, right up to the moment someone relies on it.
"""

from app.seeds.kb import Subject, load_knowledge_base

# The recorded baseline. Codes are stable identifiers that questions, blueprint
# sections and teacher assignments anchor to, so a code that disappears silently
# orphans every anchor pointing at it. Adding a subject does not touch this set;
# removing or renaming one fails the build until someone edits it deliberately
# and says why. That deliberation is the whole point — see RULE subj-004.
RECORDED_SUBJECT_CODES = frozenset(
    {
        # languages
        "HINDI", "ENGLISH", "SANSKRIT", "URDU", "MARATHI",
        # primary and middle
        "EVS", "MATHEMATICS", "SCIENCE", "SOCIAL_SCIENCE",
        # senior secondary - science
        "PHYSICS", "CHEMISTRY", "BIOLOGY", "BOTANY", "ZOOLOGY",
        "APPLIED_MATHEMATICS", "COMPUTER_SCIENCE", "INFORMATICS_PRACTICES", "BIOTECHNOLOGY",
        # senior secondary - commerce
        "ACCOUNTANCY", "BUSINESS_STUDIES", "ECONOMICS", "ENTREPRENEURSHIP",
        # senior secondary - humanities
        "HISTORY", "POLITICAL_SCIENCE", "GEOGRAPHY", "SOCIOLOGY", "PSYCHOLOGY",
        "PHILOSOPHY", "HOME_SCIENCE", "PHYSICAL_EDUCATION", "FINE_ARTS",
        # MP Board specific
        "AGRICULTURE", "CROP_PRODUCTION", "ANIMAL_HUSBANDRY", "NSQF_VOCATIONAL",
        # competitive-exam only
        "MENTAL_ABILITY", "LOGICAL_REASONING", "EVERYDAY_MATHEMATICS", "GENERAL_KNOWLEDGE",
        "CURRENT_AFFAIRS", "LEGAL_REASONING", "QUANTITATIVE_TECHNIQUES", "GENERAL_TEST",
        "ARITHMETIC", "INTELLIGENCE",
    }
)  # fmt: skip

SENIOR_SECONDARY_SCIENCES = frozenset({"PHYSICS", "CHEMISTRY", "BIOLOGY"})


def _subjects() -> tuple[Subject, ...]:
    return load_knowledge_base().subjects


def test_science_is_a_separate_subject_from_the_senior_secondary_sciences() -> None:
    """RULE subj-001: SCIENCE (6-10) is never merged with PHYSICS/CHEMISTRY/BIOLOGY (11-12).

    They are separate subjects with separate syllabus trees. An MPBSE Class 10
    Science question is not a Physics question, and the teacher who sets it is a
    different person (document 2 §4.8). Merging them would silently widen every
    Class 10 question pool with Class 12 material.
    """
    by_code = {subject.code: subject for subject in _subjects()}

    assert by_code["SCIENCE"].max_class_level == 10
    for code in SENIOR_SECONDARY_SCIENCES:
        assert by_code[code].min_class_level == 11, f"{code} must start at Class 11, not below"


def test_stream_is_set_only_on_senior_secondary_subjects() -> None:
    """RULE subj-002: a subject with a stream is taught no earlier than Class 11.

    Stream (Science / Commerce / Arts) is a senior-secondary concept. A Class 8
    student has no stream, so a stream on a subject taught below Class 11 means
    either the stream or the class range is wrong.
    """
    for subject in _subjects():
        if subject.stream is None:
            continue
        assert subject.min_class_level is not None, f"{subject.code}: stream but no class range"
        assert subject.min_class_level >= 11, (
            f"{subject.code}: stream {subject.stream} but taught from Class "
            f"{subject.min_class_level}"
        )


def test_teachability_and_class_range_agree() -> None:
    """RULE subj-003: a subject has a class range if and only if it is teachable.

    Competitive-only subjects (Mental Ability, Legal Reasoning, …) exist so
    competitive papers can be structured but are taught in no grade, so they
    carry no range and are hidden from the assignment picker (§7.4). The
    converse matters just as much: a teachable subject with no range is
    invisible to `GET /ref/subjects?class_level=`, which is a silent product
    bug rather than a loud one.
    """
    for subject in _subjects():
        has_range = subject.min_class_level is not None
        assert has_range == subject.is_teachable, (
            f"{subject.code}: is_teachable={subject.is_teachable} but "
            f"{'has' if has_range else 'has no'} class range"
        )


def test_no_recorded_subject_code_has_disappeared() -> None:
    """RULE subj-004: subject codes are append-only; none is ever renamed or removed.

    Questions anchor to subjects. Renaming `MENTAL_ABILITY` orphans every
    question mapped to it, and because the rename looks like an addition plus a
    deletion, nothing else would notice. Adding codes is free; this test only
    fires when one goes missing.
    """
    missing = RECORDED_SUBJECT_CODES - {subject.code for subject in _subjects()}

    assert not missing, (
        f"subject codes disappeared from shared/domain/subjects.yaml: {sorted(missing)}. "
        "If this is intentional, update RECORDED_SUBJECT_CODES and say why in the commit."
    )


def test_subject_hierarchy_is_at_most_one_level_deep() -> None:
    """RULE subj-005: a subject's parent never itself has a parent.

    Appendix C's only hierarchy is a parent node with trades beneath it, and the
    §7.4 picker renders exactly one level of nesting. Enforced structurally when
    the knowledge base loads; asserted here so the rule appears in the generated
    domain document alongside the others.
    """
    by_code = {subject.code: subject for subject in _subjects()}

    for subject in _subjects():
        if subject.parent is None:
            continue
        assert by_code[subject.parent].parent is None, (
            f"{subject.code} -> {subject.parent} -> {by_code[subject.parent].parent}"
        )


def test_a_child_subject_shares_its_parents_stream() -> None:
    """RULE subj-006: parent and child subjects agree on stream.

    BOTANY and ZOOLOGY sit under BIOLOGY because NEET scores four blocks while
    the syllabus publishes three subjects (document 2 §4.8). A child in a
    different stream from its parent means one of the two is misfiled.
    """
    by_code = {subject.code: subject for subject in _subjects()}

    for subject in _subjects():
        if subject.parent is None:
            continue
        parent = by_code[subject.parent]
        assert subject.stream == parent.stream, (
            f"{subject.code} is {subject.stream} but parent {parent.code} is {parent.stream}"
        )
