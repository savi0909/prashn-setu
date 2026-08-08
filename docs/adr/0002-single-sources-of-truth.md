# ADR 0002 — One specification of record, one domain knowledge base

- **Status:** Accepted
- **Date:** 2026-08-08
- **Resolves:** the v1.0/v1.1 documentation split; retires Appendix C of document 2
- **Renumbers:** DEC-18/19/20 of the deleted v1.0 log → DEC-20/21/22 of document 1 §17

## Context

Two separate duplications were discovered while designing the §5.5/§5.6
migrations. They are different in subject matter and identical in shape: a fact
stored twice, with nothing keeping the copies honest.

### 1. Two copies of the specification

`docs/IMPLEMENTATION_PLAN.md` (v1.0, combined) and the five-document set
`00-README.md` … `05-exam-creator-agent.md` (v1.1, split) were committed
together in `1f41834`. The set is the later revision and `00-README.md`
describes it as how to work; nothing said the combined file was superseded.

They had already diverged:

- **The model stack.** v1.0 specifies Sarvam-30B / Sarvam-105B. v1.1 specifies
  Gemma 4 31B Instruct on DeepMindSecure.AI, with Gemma 4 12B as the
  cross-check solver. `CLAUDE.md` still carried the v1.0 entry.
- **Document 2 §4.8 and §4.9** exist only in v1.1. §4.8 is the source of the
  subject-hierarchy requirement acted on below.
- **§5.6** differs by one line: v1.0 carries `empirical_weightage_pct`, v1.1
  does not — although v1.1's own §4.9 mandates the column and §10.2 reads it.

The damaging divergence was the decision log. The two §17s use the same
identifiers for different decisions:

| Number | v1.0 | v1.1 (authoritative) |
|---|---|---|
| DEC-18 | Corpus-first build order | DeepMindSecure.AI due diligence — open |
| DEC-19 | §5.6 schema corrections | Hindi quality on a non-Indic model — open |
| DEC-20 | `edition_sources` cardinality | *does not exist* |

ADR 0001 therefore recorded "Resolves: DEC-18" against a decision that, in the
authoritative log, is an unrelated open GPU question. Commit `88462ed`
("docs(dec-20): reframe as a cardinality question") edited only the superseded
file, so that reasoning was invisible to anyone reading the document set.

### 2. Two homes for the subject taxonomy

Appendix C of document 2 holds the subject taxonomy as markdown tables, while
§4.8 says the taxonomy "is seeded from `backend/app/seeds/subjects.yaml`". Both
would have been hand-maintained. Appendix C also carries facts that its own
table shape cannot express and that the §5.5 DDL therefore omits:

- a **Classes** column (`EVS` 1–5, `SCIENCE` 6–10, `SANSKRIT` 6–12) with no
  corresponding column in `subjects`, though §6.3 ships
  `GET /ref/subjects?class_level=`;
- `is_teachable = FALSE` for competitive-only subjects — named in the prose,
  absent from the DDL;
- `NSQF_VOCATIONAL` annotated "Parent node; trades as children", a subject-level
  hierarchy with no parent pointer anywhere.

Prose that the schema does not implement is indistinguishable from prose that it
does, right up to the moment someone relies on it.

## Decision

**Delete `docs/IMPLEMENTATION_PLAN.md`.** Git history preserves it. The
five-document set is the specification of record; `docs/00-README.md` is the
entry point. The v1.0 decisions are renumbered into document 1 §17 as DEC-20
(corpus-first), DEC-21 (§5.6 corrections), DEC-22 (edition source cardinality),
and DEC-23 (board classes as examinations, newly raised). ADR 0001's `Resolves:`
header is corrected and carries a renumbering note.

**`shared/domain/` is master for the domain knowledge base**, and is
simultaneously the source the seed loader reads. There is no second copy.

- `entities.yaml` — entity definitions, axes, and synonyms.
- `class-levels.yaml`, `subjects.yaml` — facts, machine-readable.
- `examinations/*.yaml` — one file per examination.

It lives in `shared/` rather than `backend/app/seeds/` because `ai-gateway`
prompts need the same vocabulary to ground question generation, following the
precedent already set by `shared/layout-tokens.json`.

**Rules that no row can express are Python tests, not prose.** Each carries a
`RULE <id>:` docstring — for example `RULE subj-001`, that `SCIENCE` (6–10) and
`PHYSICS`/`CHEMISTRY`/`BIOLOGY` (11–12) are distinct subjects and must never be
merged. They run in the fast unit tier and cannot pass while false.

**`docs/domain-model.md` is generated** by `make domain-docs` from the YAML plus
those harvested docstrings, and CI fails if it is stale — the guard §16.2 already
applies to `frontend/src/api/`. Appendix C of document 2 is replaced by a pointer
to it.

**Appendix C is an import, not an authority.** Its contents seed
`subjects.yaml` once. From that commit the knowledge base is master and is
expected to grow; no test asserts the two still agree.

## Consequences

**Good.** One place to read, one place to edit, and the human-readable view
cannot drift from the machine-readable one because it is derived from it. The
three schema gaps above become columns (`is_teachable`, `min_class_level` /
`max_class_level`, `parent_subject_id`) with tests, instead of prose nobody
implements. A cold session that greps `docs/` can no longer land on v1.0 and get
superseded answers.

**Bad.** Reviewing a taxonomy change now means reading YAML rather than a
rendered table, until `make domain-docs` has been run. The generated document
must be committed for that to help, which puts a regenerate step in the loop for
anyone editing the knowledge base.

**Risk to manage.** `shared/domain/` is read by a backend CLI but lives outside
`backend/`. Nothing yet guarantees it is present in the API image. Seeding is a
deploy-time operation rather than a request-path one, so this is not urgent —
but the first deployment that runs `make seed` in a container must confirm the
directory ships, or the loader gains a packaged-data fallback.
