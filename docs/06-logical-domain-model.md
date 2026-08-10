# 6 — Logical Domain Model

| Field | Value |
|---|---|
| **Document** | 6 of 6 — Logical domain model |
| **Owner** | Pratibha Mandir, Madhya Pradesh |
| **Status** | **DRAFT — product design not finalized** |
| **Version / date** | 0.1 — 8 August 2026 |

> **Implementation is frozen while this document is a draft.** No DDL, no
> migrations, no ORM models, no seed loaders until the product design is
> finalized and this document reaches version 1.0. Written deliberately without
> SQL: the point is to agree *what exists and how it relates* before arguing
> about columns.

---

## 0. The two universes

The single most useful idea to hold onto. There are two taxonomies in this
product and they meet in exactly one place.

```
   KNOWLEDGE UNIVERSE                    EXAMINATION UNIVERSE
   (stable, boardless)                   (changes every session)

   Subject                               Board
     |                                     |
   Concept / Topic                       Examination
     |                                     |
   Question  ...................>       Exam Session
                    |                      |
                    |                  Syllabus Node
                    |                      |
                    +----------------------+
                       they meet ONLY here
                    (Question <-> Syllabus Node)
```

A question about the SI unit of force is a *Physics* fact. It is not a NEET
fact or an MPBSE fact. It becomes relevant to an examination only because a
syllabus node of that examination's session covers it — and it can be covered
by many, in many examinations, in many years.

**This is why a question is never owned by an examination.** Ownership by
examination would make the same question un-storable for a second examination.

---

## 1. Layers

Three layers, never mixed. A row never moves between them.

| Layer | Contains | Mutability | Produced by |
|---|---|---|---|
| **Gold** | Official published material — syllabus documents, marking schemes, paper patterns, circulars, past papers | **Immutable.** Never edited, never re-normalised. Corrections are new rows. | Fetched from the conducting body |
| **Derived** | What machines extracted from Gold — questions, answers, topics, difficulty, observed weightage | Revisable, with an audit trail | Extraction + verification pipeline |
| **Generated** | What the platform created — predicted questions, template instances, teacher papers, explanations | Freely regenerated | Synthesis + paper generation |

The rule that makes this worth having: **a Derived or Generated row may never be
promoted to Gold.** Gold's only source is a conducting body.

---

## 2. Entities

### 2.1 Reference — the stable spine

| Entity | Is | Key relationships |
|---|---|---|
| **Board** | A body that certifies schools — MPBSE, CBSE, CISCE | conducts many **Examinations** |
| **Class Level** | A school grade, 1–12. The axis teachers describe themselves along | — |
| **Subject** | A teaching subject or exam paper component. Carries a class range, a stream, teachability, and an optional parent | may have one parent **Subject** |

### 2.2 Examination lifecycle — the backbone

This is the model to finalize first. Everything else hangs from it.

| Entity | Is | Key relationships |
|---|---|---|
| **Examination** | A permanent exam identity — NEET (UG), MPBSE Class 12. Has a *kind*: competitive, board exam, or board class (a class with a syllabus but no official paper) | belongs to a **Board** (or conducting body); has many **Exam Sessions** |
| **Exam Session** | One administration — "NEET 2026", "MPBSE session 2026-27". Boards run sessions spanning two calendar years; competitive exams run a point-in-time sitting | has one **Curriculum Snapshot**; is *historical* (has papers) or *future* (a prediction target) |
| **Curriculum Snapshot** | **Not a table — an aggregate.** Everything a session officially owns, versioned together | comprises the four entities below |
| ↳ **Syllabus Node** | A node in the Subject → Topic → Sub-topic tree, with official and observed weightage | belongs to an **Exam Session**; maps to many **Questions** |
| ↳ **Paper Pattern** | The *structure* of a paper: duration, sections, question types, counts, marks, negative marking. Contains no questions | belongs to an **Exam Session**; **optionally to one Subject** — see §3 |
| ↳ **Pattern Section** | One block within a pattern — "Section A, 20 MCQ, 1 mark each" | belongs to a **Paper Pattern**; may name a **Subject** |
| ↳ **Official Source** | One fetched official document — syllabus PDF, marking scheme, circular, sample paper. Carries URL, checksum, fetch time | belongs to an **Exam Session**; may be scoped to a **Subject** |
| **Source Paper** | An immutable ingested official booklet — "MPBSE Class 12 Physics 2023", or "NEET 2024 Code F2". Gold. Identified by session, shift and set labels, all optional because no uniform shape exists across examinations | belongs to an **Exam Session**, optionally a **Subject** |
| **Source Paper Item** | One *appearance* of a question in a source paper: its number, section, marks, options as printed | belongs to a **Source Paper** and one **Question** |

**Why Source Paper Item is separate from Question.** The same question can appear
in MPBSE 2019 *and* 2023. That repetition is the signal prediction runs on, so
appearances must be countable. A year stored on the question itself can record
only one.

**Sibling sets.** One sitting is often printed as several booklets — NEET codes
F2, G3, H4 — that share most questions in a different order. They are sibling
Source Papers, identical on session and shift and differing only by set code.
Ingesting **every** set matters twice over: sets genuinely differ in a few
questions, which are lost if only one is taken; and measuring overlap between
siblings is the best available alarm for a botched extraction. *"Set B matched
only 55% of Set A"* nearly always means the segmenter dropped questions.

**Identity needs care.** Session, shift and set labels are each absent for some
examination — JNVST has none of the three, NEET has set codes only, JEE Main has
all three. Uniqueness must therefore treat two absent labels as *the same*
absence rather than as two distinct unknowns, or the same paper ingests twice.

### 2.3 Knowledge corpus

| Entity | Is | Key relationships |
|---|---|---|
| **Question** | A reusable assessment item. Owned by the corpus, **not** by any examination or session | maps to many **Syllabus Nodes**; has translations, options, answers, explanations |
| **Question ↔ Syllabus Node** | The many-to-many that is the *only* link between corpus and examinations. One mapping is primary | — |
| **Question Group** | A shared stimulus — comprehension passage, case study, data set — with several questions under it | has many **Questions** |
| **Item Template** | A parametric problem: a stem with typed parameters, constraints, and a symbolic solution. Instantiating it yields genuinely different questions with computed answers | produces many **Questions** |
| **Question Translation** | The question's text in one locale. Hindi is a locale, **not** a version | belongs to a **Question** |
| **Question Source** | Provenance — where this question or its answer came from, and what that source asserts the answer is | belongs to a **Question** |
| **Question Review** | A verification or correction event, with old value, new value and rationale. This *is* the revision history; there is no separate version entity | belongs to a **Question** |

### Question identity — deduplication is scoped per examination

A question carries no examination and no session. But identical content is not
treated identically everywhere:

- **Within one examination, never duplicate.** Ingesting MPBSE 2019 and MPBSE
  2023 that share a question yields **one** question and **two** appearances.
  That is what makes frequency countable, and frequency is what prediction runs
  on.
- **Across examinations, a duplicate is tolerated.** MPBSE and JEE may each end
  up with their own copy of "the SI unit of force". Sharing one question between
  them is allowed and preferred; it is not required.

**The rule lives at ingestion, not in the schema.** There is no examination
column on a question and no global uniqueness constraint — either would forbid
the cross-examination copy. Before creating a question for an examination, the
pipeline checks whether one already covers that examination and reuses it if so.

**Why this is coherent.** Prediction, weightage and the exposure ledger are all
*per examination* already. A question's frequency in MPBSE is a fact about
MPBSE; JEE's copy neither adds to it nor subtracts from it.

**Two costs, accepted:**

1. **Verification is paid twice** when the same content is verified separately
   in two examination corpora. Mitigable later by linking known-identical
   questions, which nothing requires yet.
2. **Cross-examination repeats are invisible.** A coaching institute running both
   an MPBSE batch and a JEE batch — common in MP, and Anil's exact shape — could
   serve both copies to the same students. The exposure ledger is keyed by
   examination, so it will not see it. Whether that matters is a product
   question, recorded in §6.

### 2.4 Tenant and usage

| Entity | Is | Key relationships |
|---|---|---|
| **Organization** | A school or an individual teacher's synthetic org. The tenancy boundary. Carries its academic-year start month and its reuse floor | has many **Users** |
| **Generated Paper** | **The test.** Everything shared across its printed versions: the request, difficulty mix, chosen syllabus nodes, branding snapshot, base seed | pins one **Exam Session** and one **Paper Pattern**; has many **Paper Forms** |
| **Paper Form** | One printed version of the test — A, B, C. Carries its own status, marks total and credit charge | belongs to a **Generated Paper**; has many **Paper Items** and **Renditions** |
| **Paper Item** | One question's placement in a **form** — position, section, shuffled option order, marks. Marked as core or as filling a numbered swap slot | belongs to a **Paper Form** and one **Question** |
| **Question Exposure** | The reuse ledger: this organization has been served this question, for this examination, and is blocked from seeing it again until a date | links **Organization**, **Examination** and **Question** |

### Parallel forms — why the test and the paper are different things

A teacher printing a test for a hall of students wants **N versions that share
most questions but not all**, so neighbours cannot copy. That makes "the test"
and "the printed paper" two different entities, which the original model
conflated.

The shape is **common core plus unique tail**: every form contains the shared
core, and each form's remainder fills the same numbered *swap slots* with
different questions. Every question filling a given slot is matched to the others
on topic and difficulty, so the forms are genuinely equivalent rather than merely
different.

That has a consequence worth stating plainly: **a 50-question test in 3 forms at
85% shared needs 64 distinct questions, not 50.** Pool depth must be checked
against the tail count, not the paper length.

The requested share is a **target, not a guarantee** — a swap slot covers a whole
question group, because a comprehension passage must be selected and printed
atomically. CLAT is entirely passage-based, so per-question swapping would make
forms unavailable there. The solver reports what it actually achieved, and that
number is shown to the teacher rather than quietly substituted.

> **Naming.** These are **forms**, not variants. "Variant" is already taken: a
> pattern variant is a *candidate-selected* alternative, like MP PAT's Group A
> and Group B. A form is an *equivalent* alternative the candidate does not
> choose. "Parallel forms" is the psychometric term of art.

### Reuse is an exposure question, not a storage question

The corpus may hold similar questions freely — item templates produce them by
design. What must not happen is one organization seeing the same question twice
inside its repeat window.

Four rules define the ledger:

1. **Scope is the organization, not the teacher.** §1.7 describes Anil as
   *"sharply sensitive to question repeats because his students compare papers
   across batches."* Cross-batch leakage is the actual failure mode, and a
   per-teacher scope cannot see it.
2. **Scope key excludes class level.** Keying on class would leak across cohort
   progression — a question served to Class 11 in March recurring for the same
   students in Class 12 in August. The examination already implies a class band.
3. **A block lasts until the later of the academic year's end and a rolling
   floor.** Year-end aligns with cohort turnover; the floor covers questions
   served just before it. Both are per-organization settings.
4. **Exposure is recorded when a form is ready, never when it is queued.** A
   form that fails its checks refunds its credit and must not have burned its
   questions on the way out. Equally, deleting a paper does not release its
   questions — the students already saw them.

Forms of one test never count as repeats of each other; the shared core is the
point.

---

## 3. The shape that MPBSE forces

The Madhya Pradesh board is the POC, and it exposes a structural requirement
that competitive examinations hide.

**NEET**: a candidate sits **one paper** containing Physics, Chemistry, Botany
and Zoology sections, in one sitting.

**MPBSE Class 12**: a candidate sits **Physics on one day and Chemistry on
another**. Each is a separate paper with its own duration, its own total (80
marks for most subjects, 100 for Mathematics — theory only), and its own
officially published blueprint document.

So a Paper Pattern is scoped to a subject for boards and to the whole
examination for competitive exams:

```
 competitive                       board
 -----------                       -----
 Exam Session                      Exam Session
   └── Paper Pattern  (no subject)   ├── Paper Pattern — Physics
        ├── Section — Physics        ├── Paper Pattern — Chemistry
        ├── Section — Chemistry      ├── Paper Pattern — Mathematics
        ├── Section — Botany         └── ... one per subject
        └── Section — Zoology
```

One nullable subject on Paper Pattern expresses both. Absent means "one paper,
many subject sections"; present means "one paper per subject".

The same applies to Official Source: MPBSE publishes one blueprint document per
subject per session, so an official source is optionally subject-scoped too.

---

## 4. How a paper gets generated — the flow this model has to support

```
  Official documents          Past papers
  (syllabus, pattern,         (2018 … 2025)
   marking scheme)                  │
        │                           │
        ▼                           ▼
   Curriculum Snapshot ────► Source Papers (Gold, immutable)
        │                           │
        │                           ▼
        │                   Source Paper Items
        │                           │
        │                           ▼
        │                    Question Corpus (Derived)
        │                           │
        ▼                           ▼
   observed distribution:  topic frequency · marks · difficulty ·
   question type · trend over years
        │
        ▼
   Generate a realistic paper for the NEXT session
   (Generated) ── constrained by pattern, weightage, teacher's
                  chosen topics, difficulty mix, and the
                  organization's exposure ledger
        │
        ▼
   One TEST, printed as N parallel FORMS
     ├── Form A ── core questions + tail filling slots 1..n
     ├── Form B ── same core + different tail, matched slot for slot
     └── Form C ── same core + different tail
        │
        ▼
   On ready: every distinct question across ALL forms is
   written to the organization's exposure ledger
```

The generator is not inventing a paper. It is **reproducing an observed
distribution** under the current pattern. That is why the past papers are the
gold master and the syllabus alone is not enough.

---

## 4a. The corpus-depth collision — a product risk, not a schema one

Organization-wide reuse and the academic-year block are each right on their own,
and together they consume the corpus far faster than it is built. Against the
launch target of 900 verified original questions per (examination, subject),
with past-year questions not served:

| Who | Pattern | Questions/year, one subject | Pool exhausted |
|---|---|---|---|
| Sunita — MPBSE XII Chemistry | ~30 Q every 3 weeks, one form | ~510 | never |
| Rakesh's school | 3 teachers, Class 12 Chemistry, pooled org-wide | ~1,530 | ~month 7 |
| Anil — NEET weekly | 45 Physics Q per test, one form | ~2,160 | ~week 20 |
| Anil, 3 forms at 85% | 59 Q consumed per test | ~2,832 | **~week 15** |

Anil is described in §1.7 as *"the highest-value individual user."*

**The system degrades rather than fails**: when the pool runs short, the first
relaxation narrows reuse scope from the organization back to the requesting
teacher — the axis a customer notices least — before touching difficulty or
syllabus coverage. Every relaxation applied is recorded and shown to the teacher.

**What is not resolved** is whether 900 per (examination, subject) is the right
long-run target given organization-wide reuse. That is a content-operations
decision with a reviewer-day cost, and it needs a named owner.

## 5. Naming

Terms to use consistently, in code and in the UI.

| Use | Not | Why |
|---|---|---|
| **Paper Pattern** | Blueprint | MPBSE publishes a document *called* a Blueprint that is the chapter-wise **marking scheme**, not the paper structure. Two meanings, one word, in a code path that parses MPBSE PDFs. |
| **Marking scheme** (अंकयोजना) | Blueprint, weightage doc | The board's own word for it |
| **Exam Session** | Edition, year | Boards run sessions spanning two calendar years |
| **Corpus** | Question bank | The question bank is one projection of the corpus; flashcards, revision notes and tutoring are others |
| **Question** | Assessment item | Question groups already carry passages and case studies. The product is प्रश्न सेतु |
| **Paper Form** (A/B/C) | Variant | A *variant* is candidate-selected (MP PAT Group A/B). A *form* is an equivalent the candidate does not choose |
| **Exposure** | Repeat history | What is recorded is a serving event, not a property of the question |

---

## 6. Open — must be settled before this document reaches 1.0

**Knowledge representation.**

1. **Is there a Concept layer above Question?** The proposal is Subject → Concept
   → Question, with concepts stable across boards and sessions. Nothing is
   designed. It would make cross-board reuse explicit rather than implicit via
   syllabus mappings — at the cost of a second taxonomy to maintain.
2. **Is a syllabus tree per session, or shared with aliases?** Document 2 §4.3.5
   says MPSOS should reference MPBSE's tree "via a `syllabus_alias` rather than
   duplicating nodes". That mechanism is undefined and contradicts one tree per
   session. The same tension appears between examination stages that genuinely
   share a syllabus.
3. **Difficulty and Bloom level** — derived per question, or carried on the
   concept? Affects whether difficulty is a distribution to reproduce or an
   attribute to filter on.

**Examination lifecycle.**

4. **What exactly is a future session before it exists?** A prediction target
   with a pattern and a syllabus but no papers. How it is created, and by whom.
5. **Practical and internal-assessment marks.** MPBSE splits 80+20 (or 75+25);
   we serve only the objective block. Whether the pattern records the full paper
   or only the part we generate.
6. **Do examination stages share anything?** Two independent examinations, or a
   parent with stages. Stated as independent, but which pair was meant —
   Main → Advanced, or Session 1 → Session 2 — was never confirmed.

**Forms and pricing.**

7. **Does each form independently satisfy the pattern's mark total?** It should,
   but that means tail questions must be matched on marks as well as on topic
   and difficulty, which constrains the solver further.
8. **One credit per form, or per test?** Per form prices the anti-copying
   feature at 3×, which may suppress use of the feature that exists to prevent
   copying.
9. **Is 900 questions per (examination, subject) still the right target** given
    organization-wide reuse? See §4a. Content-operations decision, needs an owner.
10. **Does a cross-examination repeat matter?** Deduplication is per examination
    (§2.3), so MPBSE and JEE may hold their own copy of one question and the
    exposure ledger — keyed by examination — will not notice when an institute
    running both batches serves both copies to the same students. Anil's shape
    exactly. Accept it, or link known-identical questions across corpora.

### Resolved

- **Question identity** — deduplicate within an examination, tolerate duplicates
  across examinations, enforce at ingestion rather than in the schema. See §2.3.

### Resolved by the design note in `docs/design/`

- Exposure scope and window — organization-wide, keyed by examination, blocked
  until the later of academic-year end and a rolling floor.
- Parallel forms — common core plus topic- and difficulty-matched tails.
- Source papers — first-class, all sibling sets ingested, internal use only.

---

## 7. Not in this document

Identity, tenancy, credits, payments, notifications, rendering, OMR. Those are
settled in document 3 and unaffected by this model.

**Detailed design notes**, subordinate to this model:

- [`design/2026-08-08-forms-reuse-and-source-papers.md`](design/2026-08-08-forms-reuse-and-source-papers.md)
  — parallel forms, the reuse ledger, and source papers, worked through to
  illustrative DDL. Frozen with the rest.

**Still undesigned:** the form solver (how core and swap slots are chosen, what
happens when the pool cannot fill them), sibling-set ingestion, and the error
catalogue for form generation.

---

*Document 6 of 6. Frozen for implementation until version 1.0.*
