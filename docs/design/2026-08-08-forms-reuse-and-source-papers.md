# Domain design — parallel forms, question reuse, source papers

| Field | Value |
|---|---|
| **Status** | **Subordinate to `docs/06-logical-domain-model.md`. Frozen for implementation.** |
| **Date** | 8 August 2026 |
| **Scope** | Parallel test forms, the question-reuse ledger, and source papers |
| **Source docs** | `01-problem-actors-usecases.md` v1.1, `02-examinations-and-syllabus.md` v1.1, `03-technical.md` §5, `05-exam-creator-agent.md` §10.3 |

> **Read document 6 first.** This note is the detailed design for three clusters
> the logical model names but does not elaborate: **Paper Form**, **Question
> Exposure**, and **Source Paper**. Where the two disagree, document 6 wins —
> it is the model of record and this note predates several decisions taken on
> 8 August.
>
> **The DDL below is illustrative, not a specification.** Implementation is
> frozen until document 6 reaches v1.0 (see its §6). Three of its names have
> already changed: `paper_blueprints` → **paper patterns**, `examination_editions`
> → **exam sessions**, and `blueprint_id` → `pattern_id`.
>
> **Superseded references, corrected 8 August:**
> - `IMPLEMENTATION_PLAN.md` no longer exists. It was the v1.0 combined file and
>   was deleted; see ADR 0002. Its §17 decision numbers collided with the
>   authoritative log in document 1 §17.
> - `DEC-20` in §4 and §7 below refers to the deleted file's numbering. The
>   `edition_sources` / `edition_source_conflicts` question is now **DEC-22 and
>   is resolved** — inline primary source, corroborating-only table. See ADR 0004.
> - §4's row recommending the combined file "be retired or marked superseded" is
>   done.

---

## 1. Why this document exists

Two requirements surfaced that the existing documents do not model:

1. **Parallel test forms.** A teacher generates one test as N printed forms (A/B/C) sharing a
   tunable percentage of questions, to prevent copying in the exam hall. Nothing in §5.11
   supports this — `generated_papers` is one paper, `paper_items` keys on `paper_id`, and
   `paper_renditions` is `UNIQUE (paper_id, kind, locale)`.
2. **Organization-scoped question reuse.** Questions already served to a tenant must not
   recur for a defined period. §10.3 Stage 1 implements this per *teacher* via an
   assembled `:teacher_used_question_ids` array, with no ledger and no configurable window.

A third gap emerged while modelling the first two: **there is no entity for a real published
past paper.** "NEET 2023, Code F2" exists only as free text in `questions.origin_shift` plus
loose `question_sources` rows, so a booklet cannot be reconstructed, sibling sets cannot be
compared, and the distinct questions in sibling sets are silently discarded at ingestion.

---

## 2. Decisions

| ID | Decision | Rationale |
|---|---|---|
| **A** | `session_label`, `shift_label`, `set_code` are all nullable and vary per examination. No synthetic defaults. | JEE Main has session + shift + code; NEET has codes only; JNVST has none. §4.2 shows no uniform shape exists. |
| **B** | Examination stages are completely independent `examinations` rows. No parent-child stage relationship. | Owner's decision. UPSC Prelims/Mains and the two JEE stages get their own editions, blueprints, syllabus trees and question pools. Consequence: stages that genuinely share syllabus duplicate the tree rather than sharing it. |
| **C** | A subject is a *section* when the booklet is shared (JEE Main P/C/M), and *the paper* when candidates take a subset (CUET). Both shapes supported. | §4.2.2 vs §4.2.3. Implemented as a nullable `source_papers.subject_id`. |
| **D** | Teachers generate N **parallel forms** of one test with a tunable shared-question percentage. Named `paper_forms` / `form_code` / `form_count`. | New feature. The name `variant_code` is **already taken** by `paper_blueprints` for MP PAT's candidate-selected Group A / Group B (§4.3.4). "Parallel forms" is the psychometric term of art for alternate versions of one test. |
| **E** | Form overlap is **common core + unique tail**. Every form contains the shared core; each form has its own unique remainder. Each tail item is topic- and difficulty-matched to the slot it fills. | Symmetric, deterministic, explainable to a teacher, and the required pool depth is knowable up front. A 50Q/3-form/85% test needs 64 distinct questions, not 50. |
| **F** | Reuse blocking is **organization-wide**, not per teacher. | §1.7 describes Anil as *"sharply sensitive to question repeats because his students compare papers across batches."* Cross-batch leakage is the actual failure mode. |
| **G** | `blocked_until = MAX(end_of_academic_year, served_at + reuse_floor_days)`. | Academic-year reset aligns with cohort turnover; the rolling floor covers questions served just before year end. |
| **H** | Ledger scope key is `(organization_id, examination_id)`. Class level is **not** in the key. | Keying on class level leaks across cohort progression: a question served to Class 11 in March could recur for the same students in Class 12 in August. `examinations.entry_class` (§4.1) already implies a class band, so nothing is lost. |
| **I** | `source_papers` + `source_paper_items` are first-class, **internal use only**. Ingest every set of a sitting. | Matches DEC-17's recommendation (PYQ internal-only, gated by the `serve_pyq_questions` flag). Ingesting all sets recovers the genuinely distinct questions that `IMPLEMENTATION_PLAN.md:2851` would discard. |
| **J** | One credit per **form**. A 3-form test costs 3 credits. | Consistent with the glossary (*"1 credit = 1 paper"*). Known tension recorded in §6. |
| **K** | The relaxation ladder's first rung **narrows scope from organization to teacher**. The old first rung ("papers older than 180 days") is removed. | Resolves the corpus-depth collision in §5. The old rung is dead by construction: under G nothing ages out inside an academic year. |
| **L** | A swap slot covers an entire `question_group`. The requested shared percentage is a **target**; the solver reports what it achieved. | §4.2.4 requires passage groups to be selected and printed atomically. CLAT is 100% passage-based, so per-question swapping would make forms unavailable there entirely. |

### Structural choices

**S1 — `paper_forms` is a child of `generated_papers`.** `generated_papers` becomes *the test*,
holding everything shared (request payload, difficulty mix, syllabus nodes, branding snapshot,
base seed). `paper_forms` holds `form_code`, `charged_credits`, `status`. `paper_items` and
`paper_renditions` re-point to `form_id`.

*Rejected:* one `generated_papers` row per form linked by a family id. It duplicates
`request_payload`, `branding_snapshot` and `syllabus_node_ids` per form — drift on the first
branding edit — and has nowhere to express which questions constitute the core, which E requires.

**S2 — the reuse ledger is materialised, not derived.** Decision G makes `blocked_until` a
per-row expression; derived, it would be evaluated across the org's entire history on every
generation and could not be indexed. Materialised, it is computed once at write time and the
exclusion becomes an indexed range scan.

---

## 3. Design — entities and DDL

### 3.1 `source_papers` — the real published booklet

```sql
CREATE TABLE source_papers (
    id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    edition_id             UUID NOT NULL REFERENCES examination_editions(id),
    blueprint_id           UUID REFERENCES paper_blueprints(id),  -- shape followed, where known
    subject_id             UUID REFERENCES subjects(id),          -- set for Shape 2 (decision C)
    session_label          TEXT,                                  -- 'Session 1', 'Re-test'
    shift_label            TEXT,                                  -- 'Shift 2'
    set_code               TEXT,                                  -- 'F2' | 'B' | NULL
    exam_date              DATE,
    printed_question_count SMALLINT,
    paper_storage_key      TEXT,
    key_storage_key        TEXT,
    checksum               TEXT NOT NULL,
    ingest_confidence      NUMERIC(4,3),
    ingested_at            TIMESTAMPTZ,
    verification_state     verification_state NOT NULL DEFAULT 'UNVERIFIED',
    created_at             TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT source_papers_identity
        UNIQUE NULLS NOT DISTINCT (edition_id, subject_id, session_label, shift_label, set_code)
);
CREATE INDEX ON source_papers (edition_id, subject_id);
```

`NULLS NOT DISTINCT` (PG 15+) is required, not decorative. Postgres's default treats each NULL
as distinct, so with decision A making four columns nullable a plain `UNIQUE` would accept
`(JNVST-2023, NULL, NULL, NULL, NULL)` twice — and JNVST, having no session, shift or set, is
exactly the case where that happens.

Decision A is validated by NEET 2026, which §4.2.1 records as having had a cancellation and a
re-test: two sittings in one year, separated by `session_label`.

### 3.2 `source_paper_items`

```sql
CREATE TABLE source_paper_items (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_paper_id      UUID NOT NULL REFERENCES source_papers(id) ON DELETE CASCADE,
    position             INT NOT NULL,        -- as printed in THIS booklet
    section_code         TEXT,
    question_id          UUID NOT NULL REFERENCES questions(id),
    printed_option_order TEXT[],
    printed_marks        NUMERIC(6,2),
    UNIQUE (source_paper_id, position)
);
CREATE INDEX ON source_paper_items (question_id);
```

Deliberately the mirror of `paper_items`: the canonical question and answer live once in the
question cluster; how a given booklet ordered its options is a property of that booklet.
Ingesting Codes F2 and G3 of one sitting yields one `questions` row per distinct question
(via the existing `content_hash` unique-on-active index) and two `source_paper_items` rows.

Sibling-set overlap becomes measurable, which is the best available alarm for a botched
SEGMENT step — "Set B matched only 55% of Set A" nearly always means extraction dropped
questions:

```sql
CREATE VIEW source_paper_sibling_overlap AS
SELECT a.id AS paper_a, b.id AS paper_b,
       count(*) FILTER (WHERE ib.question_id IS NOT NULL)::numeric
         / nullif(count(*), 0) AS overlap_pct
FROM source_papers a
JOIN source_papers b
  ON  b.edition_id    = a.edition_id
  AND b.subject_id    IS NOT DISTINCT FROM a.subject_id
  AND b.session_label IS NOT DISTINCT FROM a.session_label
  AND b.shift_label   IS NOT DISTINCT FROM a.shift_label
  AND b.id > a.id
JOIN source_paper_items ia ON ia.source_paper_id = a.id
LEFT JOIN source_paper_items ib
       ON ib.source_paper_id = b.id AND ib.question_id = ia.question_id
GROUP BY a.id, b.id;
```

Siblings are rows identical on everything except `set_code`.

### 3.3 Changes to `questions`

```sql
ALTER TABLE questions DROP COLUMN origin_shift;
ALTER TABLE questions ADD COLUMN shuffle_locked BOOLEAN NOT NULL DEFAULT FALSE;
```

`origin_shift TEXT` becomes wrong once sets are ingested properly — a question printed in
Codes F2, G3 and H4 has three shifts, not one. That relationship belongs in
`source_paper_items`. `origin_year` stays: denormalised deliberately, as it is a filter
predicate on the hot selection path.

`shuffle_locked` is called for by §5.11 ("add this column") but defined nowhere.

### 3.4 `paper_forms` — decisions D, E, J, L

```sql
CREATE TABLE paper_forms (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    paper_id        UUID NOT NULL REFERENCES generated_papers(id) ON DELETE CASCADE,
    form_code       TEXT NOT NULL,                    -- 'A' | 'B' | 'C'
    display_order   SMALLINT NOT NULL,
    status          paper_status NOT NULL DEFAULT 'QUEUED',
    total_marks     NUMERIC(8,2),
    charged_credits INT NOT NULL DEFAULT 0,           -- decision J
    ready_at        TIMESTAMPTZ,
    UNIQUE (paper_id, form_code)
);
CREATE INDEX ON paper_forms (paper_id, display_order);
```

`generated_papers` gains `form_count SMALLINT NOT NULL DEFAULT 1`,
`requested_shared_pct NUMERIC(5,2)` and `achieved_shared_pct NUMERIC(5,2)` (both null when
`form_count = 1`; the pair exists because of decision L). It loses `charged_credits` and
`status` to the form.

```sql
CREATE TABLE paper_items (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    form_id         UUID NOT NULL REFERENCES paper_forms(id) ON DELETE CASCADE,
    section_code    TEXT NOT NULL,
    position        INT NOT NULL,
    question_id     UUID NOT NULL REFERENCES questions(id),
    option_order    TEXT[] NOT NULL,
    is_core         BOOLEAN NOT NULL,
    swap_slot       SMALLINT,                -- NULL if core; else which slot this fills
    marks           NUMERIC(6,2) NOT NULL,
    negative_marks  NUMERIC(6,2) NOT NULL DEFAULT 0,
    UNIQUE (form_id, position)
);
CREATE INDEX ON paper_items (question_id);

-- paper_renditions: paper_id -> form_id, UNIQUE (form_id, kind, locale)
```

`swap_slot` turns decision E from prose into a testable invariant: *for any (paper, swap_slot),
every question filling that slot across all forms shares the same primary syllabus node and the
same difficulty.* That is a property-based test over the solver requiring no database, which is
where `domain/` code belongs per the coding conventions.

`is_core` is derivable from `swap_slot IS NULL` and is kept anyway — the render and QA paths
branch on it constantly and a named boolean reads better than a null check.

### 3.5 `question_usage` — the reuse ledger, decisions F/G/H

```sql
CREATE TABLE question_usage (
    organization_id UUID NOT NULL REFERENCES organizations(id),
    examination_id  UUID NOT NULL REFERENCES examinations(id),
    question_id     UUID NOT NULL REFERENCES questions(id),
    first_served_at TIMESTAMPTZ NOT NULL,
    last_served_at  TIMESTAMPTZ NOT NULL,
    blocked_until   TIMESTAMPTZ NOT NULL,
    serve_count     INT NOT NULL DEFAULT 1,
    last_form_id    UUID REFERENCES paper_forms(id),
    PRIMARY KEY (organization_id, examination_id, question_id)
);
CREATE INDEX ON question_usage (organization_id, examination_id, blocked_until);
CREATE INDEX ON question_usage (question_id);
```

The primary key *is* decision H. Written on form transition to `READY`:

```sql
INSERT INTO question_usage AS u (organization_id, examination_id, question_id,
                                 first_served_at, last_served_at, blocked_until, last_form_id)
VALUES (:org, :exam, :qid, :now, :now, :blocked_until, :form_id)
ON CONFLICT (organization_id, examination_id, question_id) DO UPDATE
SET blocked_until = GREATEST(u.blocked_until, EXCLUDED.blocked_until),
    last_served_at = EXCLUDED.last_served_at,
    serve_count    = u.serve_count + 1,
    last_form_id   = EXCLUDED.last_form_id;
```

`first_served_at` is never updated. `blocked_until` takes `GREATEST` so a later serve can only
extend a block, never shorten it.

`blocked_until` is a pure function and belongs in `domain/` with no imports:

```python
def compute_blocked_until(
    served_at: datetime,
    academic_year_start_month: int,   # 4 = April, 6 = June
    floor_days: int,
) -> datetime:
    """max(end of the academic year containing served_at, served_at + floor_days)"""
```

`organizations` gains `academic_year_start_month SMALLINT NOT NULL DEFAULT 4` and
`reuse_floor_days INT NOT NULL DEFAULT 180`.

### 3.6 Write-ordering rules

1. **The ledger is written at `READY`, never at `QUEUED`.** A form failing §10.3 Stage 4
   refunds its credit and must not have burned its questions on the way out.
2. **Deleting or archiving a paper does not release its questions.** `blocked_until` runs its
   course regardless — the students already saw them.
3. **The forms of one test never flag each other.** `paper_repeat_flags` compares against
   *prior* papers; the shared core is not a repeat.
4. **The ledger records the union across all forms** — every distinct question in the test,
   not only those in form A.

### 3.7 Changes to §10.3 Stage 1

```sql
  -- replaces: AND q.id <> ALL(:teacher_used_question_ids)
  AND NOT EXISTS (
      SELECT 1 FROM question_usage u
      WHERE u.organization_id = :org
        AND u.examination_id  = :exam
        AND u.question_id     = q.id
        AND u.blocked_until   > now()
  )
  AND (:serve_pyq OR q.origin <> 'PYQ')      -- DEC-17 / serve_pyq_questions flag
```

### 3.8 Revised relaxation ladder (§10.3 Stage 3)

```
1. Narrow reuse scope from organization to the requesting teacher   <- decision K
2. Allow questions from archived papers
3. Widen the difficulty mix by ±10 percentage points
4. Widen to sibling syllabus nodes
5. Allow exact repeats  ← always flagged, never silent
```

The previous first rung ("allow questions from the teacher's papers older than 180 days") is
removed: under decision G nothing ages out within an academic year, so the rung can never fire.

Every relaxation applied is recorded on the paper and surfaced to the teacher.

---

## 4. Conflicts found in existing documents

These need resolving in the source documents, not only here.

| Where | Conflict | Resolution |
|---|---|---|
| `01` §1.4 | Success metric reads *"zero repeat questions against **the teacher's own history** > 98%"* | Restate organization-wide per decision F. §1.7's own description of Anil argues for org scope. |
| `01` §19 | DoD reads *"Repeat questions against **the teacher's own history** are excluded"* | Same. |
| `03` §5.11 | `paper_items.paper_id`, `paper_renditions UNIQUE (paper_id, kind, locale)` | Re-point to `form_id` per S1. |
| `03` §5.11 | Repeat detection described as per-teacher, no ledger | Replace with §3.5 and §3.7 above. |
| `05` §10.3 | Stage 1 uses `:teacher_used_question_ids`; Stage 3 rung 1 is the dead 180-day rule | Replace with §3.7 and §3.8 above. |
| `IMPLEMENTATION_PLAN.md` §10.1 | Volume table assumes *"multiple codes, same questions"* and ingests one set per sitting | Contradicts decision I. Recompute volumes for all-set ingestion. |
| `IMPLEMENTATION_PLAN.md` | Names Sarvam-30B/105B on E2E GPU throughout | Superseded — the v1.1 set uses Gemma 4 with GPU at DeepMindSecure.AI (DEC-09, DEC-18). The combined file should be retired or marked superseded. |
| `01` §17 (`DEC-20`, combined file) | `edition_sources` / `edition_source_conflicts` have no DDL, yet `02` §4.0 rule 5 and §10.4 both depend on them | Still open. Not addressed by this design. |

---

## 5. The corpus-depth collision

Decisions F, G and H are each defensible alone and jointly over-constrain the system against
**DEC-01**, which sets the launch corpus at 900 verified original questions per
(examination, subject).

Assuming 48 test-weeks and `serve_pyq_questions` **off** per DEC-17:

| Persona (§1.7) | Pattern | Questions/yr, one subject | Pool | Exhausted |
|---|---|---|---|---|
| Sunita | MPBSE XII Chemistry, ~30Q every 3 weeks, 1 form | ~510 | 900 | never |
| Rakesh's school | 3 teachers × Class 12 Chemistry, org-wide pooling | ~1,530 | 900 | ~month 7 |
| Anil | NEET weekly, 45 Physics Q/test, 1 form | ~2,160 | 900 | ~week 20 |
| Anil + 3 forms @ 85% | 59 Q consumed per test | ~2,832 | 900 | ~week 15 |

Anil is described in §1.7 as *"the highest-value individual user."*

**Resolved by decision K** — the ladder narrows scope to the requesting teacher before touching
difficulty or syllabus, so the system degrades on the axis the customer cares least about
instead of failing. No corpus change is required to ship.

**Not resolved:** whether DEC-01's 900 is the right long-run target given decision F. That is a
content-operations decision with a reviewer-day cost (DEC-15) and belongs in the decision log
with a named owner, revisited at M12 when real defect-rate data exists.

---

## 6. Known tensions accepted

- **Decision J prices the anti-copying feature at 3×.** Charging per form may suppress use of
  the feature that exists to prevent copying. Accepted by the owner; worth reviewing against
  real usage after launch.
- **Decision B duplicates syllabus trees** across stages that genuinely share syllabus
  (UPSC Prelims GS vs Mains GS).
- **Decision H doubles pool consumption** where an organization runs Class 11 and Class 12
  batches for the same examination — they now share one ledger.
- **Decision L makes the shared percentage approximate** on passage-based examinations.
  `achieved_shared_pct` must be surfaced to the teacher, never silently substituted.

---

## 7. Open questions

1. **JEE staging, unanswered.** Decision B was stated as "the two JEE stages are independent
   examinations," but which pair was meant is unconfirmed: JEE Main → JEE Advanced (two
   different examinations with a qualifying gate), or JEE Main Session 1 → Session 2 (the same
   pattern offered twice a year, best score counting). Note `02` §4.2.6 defers JEE Advanced from
   v1 entirely, which makes the first reading largely moot for now.
2. **Where `paper_purpose` interacts with forms.** A `MOCK_OFFICIAL` paper must total exactly
   `blueprint.total_marks` (§10.3 Stage 4). Whether every form must independently satisfy that
   check is undesigned — it should, but the tail questions must then be marks-matched as well as
   topic- and difficulty-matched.
3. **`edition_sources` / `edition_source_conflicts`** remain undesigned (see §4).

---

## 8. Not yet designed

- **The form solver** — how the core and swap slots are chosen under decisions E and L, what
  happens when the pool cannot fill core + tails, and how `achieved_shared_pct` is computed.
- **Ingestion of sibling sets** — how the pipeline groups booklets into a sitting and what it
  does when overlap falls outside the expected band.
- **Failure modes and error catalogue entries** for form generation.
- **Test plan.**
