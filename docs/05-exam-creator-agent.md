# 5 — Creating a Question Paper
## The Exam Creator Agent, rendering, and the OMR sheet

| Field | Value |
|---|---|
| **Document** | 5 of 5 — Exam Creator Agent |
| **Owner** | Pratibha Mandir, Madhya Pradesh |
| **Version / date** | 1.1 — 4 August 2026 |

> **Part of a five-document set.** Section numbers are preserved from the original combined plan, so a cross-reference like §9.7 stays valid across every file. If a referenced section is not in this document, find it via the map below.
>
> | § | Topic | Document |
> |---|---|---|
> | §0–§1, §6.0, §15.4, §17–§19 | Problem, actors, use cases, decisions, risks, build order | **01-problem-actors-usecases.md** |
> | §3–§4, §10.4, App. B–C | Boards, examinations, syllabus, authentic sources | **02-examinations-and-syllabus.md** |
> | §2, §5, §6–§8, §13–§16, App. D–G | Schema, APIs, web pages, notifications, infra, testing | **03-technical.md** |
> | §5.17, §9, §10.1–§10.2, §10.5, §11 | Question bank agent, verification, bilingual, explanations | **04-question-bank-agent.md** |
> | §10.3, §12 | Exam creator agent, rendering, OMR | **05-exam-creator-agent.md** |

**Read this document if** you are building the thing the teacher actually touches: turning a request into a correct, branded, unique, printable paper with a matching OMR sheet, asynchronously, with a notification when it is ready.

**Section index**

| § | Contents |
|---|---|
| §5.0 | The shape of the problem, and why it is not an LLM call |
| §10.3 | The Exam Creator Agent — pool, solver, repeats, checks, instructions |
| §12 | Rendering: engine, layout tokens, OMR sheet, bilingual layout |

The teacher-facing UI for this flow (the creation wizard, the preview pane, repeat flags) is in document 3, §7.5–§7.6. The API contract is document 3, §6.4. The corpus this agent draws from is document 4.

---

## 5.0 The shape of the problem

A teacher's request is a set of hard constraints:

- Exactly *N* questions, split across sections in exactly the counts the blueprint specifies.
- A difficulty mix that must sum to the total.
- Coverage spread across the selected syllabus nodes in proportion to weightage.
- Zero questions the teacher has used before, where the pool allows it.
- Marks that total exactly what the paper claims.
- Every item present in every requested language.

**This is a constrained-selection problem, and it must be solved as one.** Per architectural decision AD-1 (document 3, §2.2), the Exam Creator does **not** ask an LLM to "pick 45 physics questions". Language models are unreliable at exact-count constraints and, worse, unauditable when they fail — you cannot ask a prompt why it produced 44 questions instead of 45. A solver is deterministic, fast, testable, seedable, and can explain precisely which constraint it could not satisfy.

The LLM's role in paper creation is narrow and peripheral: rendering the instruction block in the right language and register, and a final sanity review. **Explanations are not generated here** — they were written once, at corpus time, and are simply retrieved. That is the payoff for the up-front investment in document 4, and it is why paper generation costs no GPU and scales with teachers for free.

### What "correct" means for a paper

Requirement: *"checks the paper for correctness in terms of duration of examination, number of questions, correct answers, instructions to be printed, language of paper."* Made concrete, that is the eleven-check table in §10.3, Stage 4. Hard failures fail the job and refund the credit; soft failures auto-repair.

### Latency budget

Target p50 under 90 seconds, p95 under 4 minutes for a 45-question bilingual paper with an OMR sheet. The solver itself is milliseconds. Effectively all of the time is rendering.

---

### 10.3 Exam Creator Agent

**Goal (requirement #13):** take teacher input and produce a correct, branded, unique paper with an OMR sheet, asynchronously, with notification on completion.

Per **AD-1**, selection is a solver, not a prompt.

**Stage 1 — Build the eligible pool** (per section):

```sql
SELECT q.id, q.difficulty, qsm.node_id, qe.embedding
FROM questions q
JOIN question_syllabus_map qsm ON qsm.question_id = q.id
JOIN question_embeddings qe ON qe.question_id = q.id
JOIN syllabus_nodes sn ON sn.id = qsm.node_id
WHERE q.examination_id = :exam
  AND q.subject_id = :subject
  AND q.is_active
  AND q.verification_state = 'VERIFIED'
  AND q.question_type = :qtype
  AND sn.path <@ ANY(:selected_paths)
  AND EXISTS (SELECT 1 FROM question_translations t
              WHERE t.question_id = q.id AND t.locale = ANY(:locales))
  AND q.id <> ALL(:teacher_used_question_ids)   -- hard repeat exclusion
```

**Stage 2 — Constrained selection.** Objective: hit the difficulty mix and spread across selected syllabus nodes proportionally to their weightage, while maximising minimum pairwise embedding distance (topical variety).

Implementation: greedy with a repair pass, which is fast enough and easy to test.

```python
def select(pool, count, difficulty_mix, node_weights, rng, prior_embeddings):
    quotas = largest_remainder(count, difficulty_mix)          # {EASY:9, MEDIUM:15, HARD:6}
    node_quota = largest_remainder(count, node_weights)
    chosen: list[Question] = []
    for difficulty, n in quotas.items():
        bucket = [q for q in pool if q.difficulty == difficulty]
        # weight by node deficit, penalise similarity to prior papers and to chosen
        for _ in range(n):
            scored = [
                (score(q, node_quota, chosen, prior_embeddings), q)
                for q in bucket if q not in chosen
            ]
            if not scored:
                raise InfeasibleSection(difficulty=difficulty, short_by=n - ...)
            chosen.append(weighted_sample(scored, rng))
    return repair(chosen, quotas, node_quota, rng)
```

`rng` is seeded from `generated_papers.seed`, so **the same request produces the same paper**. This makes the whole thing testable and makes "regenerate" meaningfully different (new seed) rather than accidentally identical.

**Stage 3 — Repeat detection** (requirement #13's flagging behaviour). Exact repeats are excluded in Stage 1. But if exclusion makes a section infeasible, the solver relaxes in a defined order and records what it relaxed:

```
1. Allow questions from the teacher's papers older than 180 days
2. Allow questions from archived papers
3. Widen the difficulty mix by ±10 percentage points
4. Widen to sibling syllabus nodes
5. Allow exact repeats  ← always flagged, never silent
```

Near-duplicates (cosine ≥ 0.88 against the teacher's prior papers) are always flagged, never excluded. Each flag names the prior paper and its date.

**Stage 4 — Correctness checks on the assembled paper.** These are the "checks the paper for correctness" requirement, made concrete:

| Check | Rule |
|---|---|
| Question count | `len(items) == sum(section.question_count)` |
| Marks total | `Σ(marks) == blueprint.total_marks` (for `MOCK_OFFICIAL`) |
| Duration sanity | ≥ 45 s/question for MCQ, ≥ 100 s/question for numeric; warn outside band |
| Answer key balance | No single option label holds > 40% or < 10% of answers |
| Answer key runs | No run of 5+ identical consecutive answers |
| Duplicate within paper | No question id twice; no pairwise cosine ≥ 0.92 |
| Translation completeness | Every item has all requested locales for stem, options and (if included) solutions |
| Asset resolution | Every `{{asset:n}}` reference resolves to a stored file |
| Shuffle safety | `shuffle_locked` questions retain canonical order |
| Section timing | If `sectional_timing`, per-section minutes sum to `duration_minutes` |
| Instruction language | Instructions rendered in each requested locale |

Any hard failure → the job fails, the credit is refunded, and the teacher gets a plain-language reason. Soft failures (answer-key balance) → auto-repair by reshuffling `option_order` and re-checking.

**Stage 5 — Instructions.** Generated per examination, per locale, per purpose from a template plus an LLM polish pass. They must state: number of questions, total marks, duration, marking scheme including negative marking (or its absence — MP PAT and NMMS have none, and a student who assumes otherwise loses marks by not guessing), OMR filling rules, sectional timing where applicable, and permitted materials.

For MP PAT specifically the instruction block must state the group (A or B). For JNVST it must state that section times cannot be pooled.

**Stage 6 — Render** → hand off to the render pipeline (§12).

**Stage 7 — Notify** → `PAPER_READY`.

**Target latency:** p50 under 90 s, p95 under 4 min for a 45-question bilingual paper with OMR. The solver is milliseconds; the time is rendering and, if solutions are requested, nothing — explanations are pre-generated and stored, not generated at paper time. This is the payoff for the up-front bank investment.

---

## 12. Document generation

### 12.1 Outputs per paper

| Rendition | Contents |
|---|---|
| `QUESTION_PDF` | Branded question paper, per locale (or one bilingual document) |
| `ANSWER_KEY_PDF` | Compact grid: question number → correct option, plus marks scheme |
| `SOLUTIONS_PDF` | Every question with all three explanation tiers |
| `OMR_PDF` | Machine-readable answer sheet matching the paper's structure |
| `DOCX` | Editable Word version, for teachers who want to tweak |

### 12.2 Rendering engine

**Primary: Typst.** Fast (sub-second for a 20-page document versus several seconds for LaTeX), scriptable, good Unicode and OpenType handling, and a sane programmatic API — which matters because we are generating templates from data, not hand-authoring. Devanagari support via Noto Serif Devanagari.

**Fallback: XeLaTeX.** Kept because it is the most battle-tested path for complex mathematics plus Devanagari in one document, and because Pratibha Mandir's existing production knowledge is in that world. Selected by a per-organization config flag so a single problematic paper can be re-rendered on the other engine without a deploy.

**DOCX: `python-docx` with a custom LaTeX→OMML converter.** Word's native equation format is OMML; embedding images of equations produces a document nobody can edit, which defeats the purpose. Fonts: Noto Serif Devanagari for Devanagari runs, with explicit `w:rFonts` `cs`/`eastAsia` attributes set — Word's font fallback for mixed-script runs is unreliable and must be pinned per run.

**Never** render PDFs with a headless browser. Print CSS gives poor control over widow/orphan behaviour across a two-column question paper, page-break avoidance inside a question-plus-diagram block, and Devanagari line-breaking. This will be tempting because the web preview already exists; resist it.

### 12.3 Layout tokens

Layout constants live in one JSON file consumed by both the web preview and the PDF renderer, so the preview cannot drift from the output:

```jsonc
// shared/layout-tokens.json
{
  "page": { "size": "A4", "margin_mm": { "top": 18, "bottom": 16, "inner": 16, "outer": 12 } },
  "columns": { "count": 2, "gutter_mm": 6 },
  "type": {
    "stem":        { "size_pt": 10.5, "leading_pt": 14.5, "hi_leading_pt": 16.5 },
    "option":      { "size_pt": 10.0, "leading_pt": 13.5, "hi_leading_pt": 15.5 },
    "section_head":{ "size_pt": 12.0, "weight": "bold" }
  },
  "fonts": {
    "latin_serif": "Noto Serif",
    "devanagari_serif": "Noto Serif Devanagari",
    "math": "Latin Modern Math"
  },
  "rules": {
    "keep_question_with_options": true,
    "keep_diagram_with_stem": true,
    "min_orphan_lines": 2,
    "max_diagram_width_mm": 70
  }
}
```

**`keep_question_with_options` and `keep_diagram_with_stem` are the two rules that make a paper look professional.** A question stem at the foot of a column with its options overleaf is the classic amateur tell, and it genuinely disadvantages students.

### 12.4 The OMR sheet

Generated to a scannable specification even though scanning is a v2 feature — retro-fitting a spec to sheets already in circulation is not possible.

**Specification:**

| Element | Spec |
|---|---|
| Page | A4 portrait, single sheet where question count allows |
| Fiducial markers | Four solid 8 mm squares at 10 mm inset from each corner, for deskew and perspective correction |
| Timing marks | 4 mm × 2 mm marks down the left edge, one per bubble row, for row registration |
| Bubble | 4.2 mm diameter circle, 1.0 mm stroke, 3.0 mm inter-bubble gap |
| Row pitch | 8.0 mm |
| Roll number | Grid of digit columns, 10 bubbles each; column count from the exam's roll-number length |
| Booklet code | Where the exam uses paper sets |
| Question blocks | Columns of 25 or 30 rows; block header shows the range |
| Numeric entry (JEE Main Section B) | Per question: a sign cell (+/−), 5 digit columns and a decimal-point column, each 10 bubbles |
| Print margin | 8 mm bleed-free zone; a warning if the branding header would encroach |
| Registration text | Human-readable paper id + a Code-128 barcode encoding `paper_id` |
| Instructions | "Use a black or blue ball pen. Fill the bubble completely. Do not use pencil or whitener." — in both locales |

**Layout is derived from the blueprint, not hardcoded.** A 180-question NEET sheet is very different from a 20-question MPBSE objective test and a 45-question practice set. Compute rows-per-column and column count from question count and page geometry, and spill to a second page only when necessary.

**Options-count varies.** Most Indian MCQ exams use 4 options; the generator must read `options_count` from the section, not assume 4.

**Answer key export for scanning.** Alongside the OMR PDF, emit `answer_key.json`:

```jsonc
{
  "paper_id": "…",
  "version": 1,
  "omr_spec_version": "1.0",
  "sections": [{"code": "PHY", "range": [1, 45], "marks": 4, "negative": 1}],
  "answers": [
    {"q": 1, "type": "MCQ_SINGLE", "correct": ["B"]},
    {"q": 46, "type": "NUMERIC", "correct_value": 12.5, "tolerance": 0.1}
  ]
}
```

Note `correct` is an array — this costs nothing now and is what makes multiple-correct questions possible later without a format break.

### 12.5 Bilingual layout

⚠️ **DEC-02:** two viable presentations. Support both; default per organization.

- **(a) Facing/stacked** — each question shows English then Hindi, in one document. Standard for NTA and MPESB papers. Doubles page count. Best when a class is mixed-medium.
- **(b) Separate documents** — one Hindi PDF, one English PDF, sharing question numbering and one OMR sheet. Half the paper, cleaner to read.

Default **(b)**, since a Hindi-medium class does not need the English. Offer (a) explicitly, and default to (a) for examinations that are themselves administered bilingually in one booklet (MP PAT, NEET).

In presentation (a), the Hindi block is visually subordinated (a hairline left rule, slight indent) so the eye can lock to one language and skim. Do not simply alternate two identical-weight paragraphs.

### 12.6 Rendering performance and safety

- Render in a **sandboxed subprocess** with CPU, memory and wall-clock limits. Typst and TeX are both capable of pathological runtime on malformed input.
- Cache the compiled template per branding profile; only the content varies per paper.
- Fonts are baked into the render container image, not fetched at runtime.
- Every rendition's checksum is stored; a re-render that produces a different checksum for the same `(paper_id, seed)` is a bug and should alert. Determinism includes setting a fixed PDF creation date and disabling any embedded timestamp.

---

## 12.7 Failure handling, end to end

| Failure | Detected at | Behaviour |
|---|---|---|
| Pool too small for the request | `POST /papers/estimate`, before charging | 422 with per-section shortfall and a suggested feasible alternative. **No credit charged, no job created.** |
| Pool became too small between estimate and submit | Validation, before charging | Same 422 path |
| Solver cannot satisfy after the full relaxation ladder | Stage 2 | Job fails, credit refunded, plain-language reason naming the constraint |
| A hard paper check fails | Stage 4 | Job fails, credit refunded, alert raised — this is a bug, not a user error |
| A soft check fails (answer-key balance) | Stage 4 | Auto-repair by reshuffling `option_order`, re-check, continue |
| Render engine timeout or crash | Stage 6 | Retry once on the fallback engine (§12.2); if both fail, job fails and credit is refunded |
| Missing asset for a selected question | Stage 4 | Question is swapped out and the item is flagged for content review |
| Notification send fails | Stage 7 | Paper is still `READY` and visible in the workspace; notification retries independently. **A failed SMS must never mark a paper failed.** |

The rule underneath all of these: **a teacher never loses a credit to our bug.** Refund automatically and tell them why, in their own language.

---

*Document 5 of 5. Back to `01-problem-actors-usecases.md`.*
