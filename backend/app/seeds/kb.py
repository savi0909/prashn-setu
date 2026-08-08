"""Typed reader for the domain knowledge base in ``shared/domain/``.

The knowledge base is master (ADR 0002), so these models are the only thing
between a typo in a YAML file and a bad seed run. Every model forbids unknown
keys: a misspelt field must fail loudly rather than be silently dropped.
"""

from collections import Counter
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any, Literal, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

# `shared/`, not `backend/app/seeds/`: the ai-gateway prompts need this same
# vocabulary to ground question generation, following the precedent set by
# shared/layout-tokens.json. Resolved from this module rather than the cwd so
# `make seed` (cwd=backend) and `pytest` (cwd=backend) and a container entry
# point all find the same files.
DOMAIN_DIR = Path(__file__).resolve().parents[3] / "shared" / "domain"

# Codes are stable identifiers that questions and blueprint sections anchor to
# (document 2, Appendix C: "never renumber"). Pinning the shape is what turns
# RULE subj-004 — codes never change — from an aspiration into something a test
# can check, since a code that cannot be lower-cased or hyphenated cannot drift
# into a near-miss of itself.
SubjectCode = Annotated[str, StringConstraints(pattern=r"^[A-Z][A-Z0-9_]*$")]

# Indian schooling runs 1-12. There is no Class 0 and no Class 13.
ClassLevelId = Annotated[int, Field(ge=1, le=12)]

# §5.5's vocabulary. Stream is a senior-secondary concept only; Appendix C sets
# it on Classes 11-12 subjects and leaves it NULL everywhere else.
Stream = Literal["SCIENCE", "COMMERCE", "ARTS"]


class KnowledgeBaseModel(BaseModel):
    """Shared configuration for every knowledge-base record.

    ``frozen`` because these are parsed facts, not working state — a caller that
    mutates one has misunderstood where the truth lives.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)


class ClassLevel(KnowledgeBaseModel):
    """One school grade. §5.5 keys these by the integer itself, 1 through 12."""

    id: ClassLevelId
    name_en: str
    name_hi: str


class Subject(KnowledgeBaseModel):
    """One subject in the taxonomy (document 2, Appendix C)."""

    code: SubjectCode
    name_en: str
    name_hi: str
    stream: Stream | None = None

    # Competitive-only subjects (Mental Ability, Legal Reasoning, …) exist so
    # competitive papers can be structured, but have no class-level teaching
    # equivalent and must never reach the teacher-assignment picker
    # (document 2, §4.8). They are the minority, so TRUE is the quiet default.
    is_teachable: bool = True

    # Appendix C gives every taught subject a contiguous class range — EVS 1-5,
    # SCIENCE 6-10, SANSKRIT 6-12 — which two bounds express exactly. Both NULL
    # for competitive-only subjects, which are taught in no grade at all.
    min_class_level: ClassLevelId | None = None
    max_class_level: ClassLevelId | None = None

    # Named by code, not id: the knowledge base has no UUIDs in it. The loader
    # resolves this to `parent_subject_id` once both rows exist. Appendix C's
    # NSQF_VOCATIONAL is the case that needs it — "parent node; trades as
    # children".
    parent: SubjectCode | None = None

    # The teacher-assignment picker is subject-first (§7.4), so ordering is a
    # product concern. 1000 sinks anything that has not been placed.
    sort_order: int = 1000

    @model_validator(mode="after")
    def _class_range_is_coherent(self) -> Self:
        low, high = self.min_class_level, self.max_class_level

        # Both or neither. One bound alone has no defensible meaning: it reads
        # as "taught from Class 6 upward" only if you assume an open interval
        # nobody wrote down.
        if (low is None) != (high is None):
            raise ValueError(
                f"{self.code}: min_class_level and max_class_level must be set together"
            )

        if low is not None and high is not None and low > high:
            raise ValueError(f"{self.code}: min_class_level {low} exceeds max_class_level {high}")

        return self


class Entity(KnowledgeBaseModel):
    """A domain term, what it means, and what else it gets called.

    ``aka`` earns its place beyond documentation: the ai-gateway prompts ground
    on these terms, and a teacher who types "standard 9" means class level 9.
    """

    name: str
    aka: tuple[str, ...] = ()
    definition: str


class KnowledgeBase(KnowledgeBaseModel):
    """Everything in ``shared/domain/``, parsed and structurally checked.

    Structural integrity lives here so that *nothing* — loader, doc generator or
    test — can obtain a broken knowledge base. Semantic rules (SCIENCE is not
    PHYSICS, stream implies senior secondary) live in ``tests/unit/domain_rules``
    instead, where each carries its own ``RULE`` identifier and explanation.
    """

    entities: tuple[Entity, ...]
    class_levels: tuple[ClassLevel, ...]
    subjects: tuple[Subject, ...]

    def subject_by_code(self, code: str) -> Subject:
        for subject in self.subjects:
            if subject.code == code:
                return subject
        raise KeyError(f"no subject with code {code!r} in {DOMAIN_DIR}")

    @model_validator(mode="after")
    def _codes_are_unique(self) -> Self:
        counts = Counter(subject.code for subject in self.subjects)
        duplicates = sorted(code for code, count in counts.items() if count > 1)
        if duplicates:
            raise ValueError(f"duplicate subject codes: {', '.join(duplicates)}")
        return self

    @model_validator(mode="after")
    def _parents_resolve_and_nest_one_level(self) -> Self:
        """A named parent must exist, and the hierarchy is at most one deep.

        Appendix C's only hierarchy is a parent node with trades beneath it, and
        §7.4's picker renders one level of nesting. Anything deeper is a data
        error, not a feature — catch it here rather than in the UI.
        """
        by_code = {subject.code: subject for subject in self.subjects}

        for subject in self.subjects:
            if subject.parent is None:
                continue

            parent = by_code.get(subject.parent)
            if parent is None:
                raise ValueError(
                    f"{subject.code}: parent {subject.parent!r} is not a known subject"
                )
            if parent.code == subject.code:
                raise ValueError(f"{subject.code}: is its own parent")
            if parent.parent is not None:
                raise ValueError(
                    f"{subject.code}: parent {parent.code} itself has a parent — "
                    "the subject hierarchy is at most one level deep"
                )

        return self


class _EntitiesFile(KnowledgeBaseModel):
    version: int
    entities: tuple[Entity, ...]


class _ClassLevelsFile(KnowledgeBaseModel):
    class_levels: tuple[ClassLevel, ...]


class _SubjectsFile(KnowledgeBaseModel):
    subjects: tuple[Subject, ...]


def _read_yaml(filename: str) -> Any:
    # encoding is explicit because every one of these files is half Devanagari
    # and Python on Windows would otherwise open them as cp1252.
    with (DOMAIN_DIR / filename).open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


@lru_cache(maxsize=1)
def load_knowledge_base() -> KnowledgeBase:
    """Parse and validate ``shared/domain/``.

    Cached: the files do not change within a process, and the seed loader, the
    doc generator and the rule tests all want the same parsed copy.
    """
    return KnowledgeBase(
        entities=_EntitiesFile.model_validate(_read_yaml("entities.yaml")).entities,
        class_levels=_ClassLevelsFile.model_validate(_read_yaml("class-levels.yaml")).class_levels,
        subjects=_SubjectsFile.model_validate(_read_yaml("subjects.yaml")).subjects,
    )
