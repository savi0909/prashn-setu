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
| **Source Paper** | An immutable ingested official paper — "MPBSE Class 12 Physics, 2023". Gold | belongs to an **Exam Session** and a **Subject** |
| **Source Paper Item** | One *appearance* of a question in a source paper: its number, section, marks, options as printed | belongs to a **Source Paper** and one **Question** |

**Why Source Paper Item is separate from Question.** The same question can appear
in MPBSE 2019 *and* 2023. That repetition is the signal prediction runs on, so
appearances must be countable. A year stored on the question itself can record
only one.

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

### 2.4 Tenant and usage

| Entity | Is | Key relationships |
|---|---|---|
| **Organization** | A school or an individual teacher's synthetic org. The tenancy boundary | has many **Users** |
| **Generated Paper** | A paper the platform assembled for an organization, targeting a session and following a pattern | pins one **Exam Session** and one **Paper Pattern** |
| **Paper Item** | One question's placement in a generated paper — position, section, shuffled option order, marks | belongs to a **Generated Paper** and one **Question** |
| **Question Exposure** | The reuse ledger: this organization has seen this question, on this date | links **Organization** and **Question** |

**Duplication is a serving concern, not a storage concern.** The corpus may hold
similar questions freely — that is what item templates produce by design. What
must not happen is one organization seeing the same question twice inside its
repeat window. That is a question about exposure events, not about rows.

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
```

The generator is not inventing a paper. It is **reproducing an observed
distribution** under the current pattern. That is why the past papers are the
gold master and the syllabus alone is not enough.

---

## 5. Naming

Terms to use consistently, in code and in the UI.

| Use | Not | Why |
|---|---|---|
| **Paper Pattern** | Blueprint | MPBSE publishes a document *called* a Blueprint that is the chapter-wise **marking scheme**, not the paper structure. Two meanings, one word, in a code path that parses MPBSE PDFs. |
| **Marking scheme** (अंकयोजना) | Blueprint, weightage doc | The board's own word for it |
| **Exam Session** | Edition, year | Boards run sessions spanning two calendar years |
| **Corpus** | Question bank | The question bank is one projection of the corpus; flashcards, revision notes and tutoring are others |
| **Question** | Assessment item | Question groups already carry passages and case studies. The product is प्रश्न सेतु |

---

## 6. Open — must be settled before this document reaches 1.0

1. **Is there a Concept layer above Question?** The proposal is Subject → Concept
   → Question, with concepts stable across boards and sessions. Nothing is
   designed. It would make cross-board reuse explicit rather than implicit via
   syllabus mappings — at the cost of a second taxonomy to maintain.
2. **Is a syllabus tree per session, or shared with aliases?** Document 2 §4.3.5
   says MPSOS should reference MPBSE's tree "via a `syllabus_alias` rather than
   duplicating nodes". That mechanism is undefined and contradicts one tree per
   session.
3. **Difficulty and Bloom level** — derived per question, or carried on the
   concept? Affects whether difficulty is a distribution to reproduce or an
   attribute to filter on.
4. **What exactly is a future session before it exists?** A prediction target
   with a pattern and a syllabus but no papers. How it is created, and by whom.
5. **Exposure window** — organization-wide or per teacher, and what default.
6. **Practical and internal-assessment marks.** MPBSE splits 80+20 (or 75+25);
   we serve only the objective block. Whether the pattern records the full paper
   or only the part we generate.

---

## 7. Not in this document

Identity, tenancy, credits, payments, notifications, rendering, OMR. Those are
settled in document 3 and unaffected by this model.

---

*Document 6 of 6. Frozen for implementation until version 1.0.*
