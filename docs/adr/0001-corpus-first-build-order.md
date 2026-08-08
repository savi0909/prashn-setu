# ADR 0001 — Corpus-first build order

- **Status:** Accepted
- **Date:** 2026-08-07
- **Resolves:** DEC-20 (document 1, §17)
- **Supersedes:** the milestone sequence in §15.4 for M1–M4 only

> **Renumbered 2026-08-08.** This ADR originally read "Resolves: DEC-18",
> referring to the decision log in `docs/IMPLEMENTATION_PLAN.md` — the v1.0
> combined document, since deleted. In the authoritative log (document 1, §17)
> DEC-18 is DeepMindSecure.AI due diligence, an unrelated open question. The
> corpus-first decision is DEC-20 there. Section references below point at the
> five-document set. See ADR 0002.

## Context

§15.4 sequences the build M0 → M1 (identity and tenancy) → M2 (OTP and
notifications) → M3 (teachers, assignments, branding) → M4 (reference data) →
M5 (question schema). Reference data and the question schema — the examination
catalogue and the corpus — arrive in weeks 5 and 6.

`CLAUDE.md` states the corpus is the asset: "what takes eighteen months to build
and what a competitor cannot copy in a weekend." Those two statements imply
different starting points. §15.4 is a portal-first ordering; the product thesis
is corpus-first.

The deciding technical fact is that the corpus has no tenancy. Searching the
whole of §5 for `organization_id`:

- **Present on:** `generated_papers`, `branding_profiles`, `credit_accounts`,
  `credit_ledger`, `payments`, `jobs`, `audit_events`, `notifications`.
- **Absent from:** every table in §5.6 (`examinations`, `examination_editions`,
  `paper_blueprints`, `blueprint_sections`, `syllabus_nodes`) **and** every
  table in §5.7–§5.11 (`questions`, all translation tables, `question_options`,
  `question_answers`, `question_explanations`, `question_assets`,
  `question_sources`, `question_reviews`, `question_embeddings`).

The examination catalogue and the entire question bank are global platform
assets. They therefore have no dependency on identity, tenancy, RLS, OTP,
credits, or branding.

## Decision

Build in this order:

1. **M0-lite** — Compose (Postgres 16 + pgvector + ltree + pgcrypto + citext,
   Redis, MinIO), Alembic, FastAPI skeleton, ruff/mypy/pytest, CI, pre-commit,
   structured logging, health endpoints, one end-to-end test. Frontend skeleton
   deferred.
2. **§5.5 subset** — `class_levels` and `subjects` only. These are the sole
   upstream dependency of §5.6 and are small, static and seedable
   (Appendix C).
3. **§5.6** — examinations, editions, blueprints, sections, syllabus tree, with
   the corrections in DEC-19 and DEC-20 applied first.
4. **§5.7–§5.11** — the question schema.

M1 (identity and tenancy), M2 (OTP) and M3 (teachers, branding) are deferred,
not cancelled.

`examination_editions.approved_by` references `users(id)`. The column is
nullable, so the FK is added when §5.3 lands rather than blocking §5.6.

## Consequences

**Good.** The riskiest and slowest-to-build asset starts in week 1 instead of
week 6. Schema decisions in §5.6/§5.7 get validated against real seed data
before any auth surface is built on top of them. The work needs no MSG91, no
Razorpay and no DLT approval, all of which have external lead times.

**Bad.** There is nothing demonstrable to a school until M8. If a pilot
conversation needs a screen before then, this ordering is wrong and §15.4 as
written is right.

**Risk to manage.** §13.3 specifies a schema-guard test that enumerates every
SQLAlchemy model with an `organization_id` column and asserts a matching RLS
policy exists. Deferring M1 defers that test. The first tenant-owned table is
`generated_papers` at M6, so **the schema guard and the tenancy repository base
must land before M6 begins** — not "with M1, whenever that happens." If a
tenant-owned table is introduced earlier for any reason, M1 comes forward with
it.

§15.4 has not been rewritten; this ADR is the amendment of record for M1–M4.
