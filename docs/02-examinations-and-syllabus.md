# 2 — Boards, Examinations, Subjects and Syllabus
## Where the content comes from, and how we know it is right

| Field | Value |
|---|---|
| **Document** | 2 of 5 — Domain reference and authentic sources |
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

**Read this document if** you are seeding reference data, deciding which examination to build content for next, or building the pipeline that keeps syllabus data current. It answers three questions: *which examinations matter in Madhya Pradesh, what is inside each of them, and where does authentic information about them actually come from.*

**The single most important idea in this document is §4.0.** Every number here is a starting hypothesis, not a fact. Exam patterns change annually and sometimes mid-cycle, and a question bank mapped to a stale pattern is worse than no bank at all.

---

## 4.0 Epistemic rules — read before using any number in this document

This section is a **research-informed seed**, not an authority. Exam patterns change annually and sometimes mid-cycle. Two concrete examples from the current cycle prove the point:

- **JEE Main** removed the optional-questions facility in Section B from the 2025 cycle onward: each subject now has 5 numerical-value questions that are all compulsory, where previously candidates chose 5 of 10 — and negative marking now applies to Section B, which it did not before. Third-party coaching sites still carry the old rule.
- **JNVST Class 6** restructured Section 1 to combine Mental Ability with a new Environmental Studies component. Any question bank mapped to the old three-section structure is now mis-mapped.

Therefore:

1. Every `examination_edition` row carries `source_url`, `source_fetched_at`, `source_checksum`, and `verification_state`.
2. No edition is served to teachers in `UNVERIFIED` state. A super admin must approve it (§10.4).
3. Numbers marked 🔍 in the tables below are seeded as `UNVERIFIED` and **must** be confirmed against the official information brochure / prospectus / rule book before the exam is enabled.
4. The ToC Refresh Agent (§10.4) runs annually and produces a *diff* for human approval. It never silently overwrites.
5. When the official source and a coaching-site source disagree, the official source wins and the disagreement is logged to `edition_source_conflicts` for audit.

---

## 3. Master data: school boards

A school selects **one or more** board affiliations at signup. This drives (a) which examinations are surfaced by default, (b) which syllabus versions are preferred, and (c) branding copy defaults.

### 3.1 Important modelling nuance — board vs. certification

`ICSE` is **not** a board. It is a Class 10 certification issued by CISCE. CISCE issues:
- **ICSE** — Indian Certificate of Secondary Education (Class 10)
- **ISC** — Indian School Certificate (Class 12)
- **CVE** — Certificate for Vocational Education

Teachers colloquially say "ICSE board", so the UI **SHOULD** display "CISCE (ICSE / ISC)" and accept "ICSE" as a search alias. The database models `boards` and `board_certifications` separately (§5.4). The same applies to CBSE ("AISSE" Class 10 / "AISSCE" Class 12) and to the international boards.

### 3.2 National boards (seed set)

| Abbrev | Full name | Established | HQ | Notes |
|---|---|---|---|---|
| CBSE | Central Board of Secondary Education | 1929 (as board), 1962 as CBSE | New Delhi | Largest national board; NCERT-aligned; feeds JEE/NEET/CUET directly |
| CISCE | Council for the Indian School Certificate Examinations | 1958 | New Delhi | Private non-governmental national board; conducts ICSE (X), ISC (XII) |
| NIOS | National Institute of Open Schooling | 1989 | Noida, UP | Open-schooling; largest open-schooling system; secondary + senior secondary |

### 3.3 International boards (seed set)

| Abbrev | Full name | Programmes relevant to ≤ Class 12 |
|---|---|---|
| IB | International Baccalaureate | PYP, MYP, DP, CP |
| CAIE | Cambridge Assessment International Education | Cambridge Primary, Lower Secondary, IGCSE, AS & A Level |
| PEARSON | Pearson Edexcel International | International GCSE, International A Level |

Note: CAIE is a University of Cambridge body headquartered in the UK; IB is a Geneva-headquartered non-profit. Neither has an Indian regulatory relationship with MPBSE. They are included because MP metros (Indore, Bhopal) have IB/CAIE schools that may want branded MCQ practice sets, but **no examination content is seeded for these boards in v1** — see §4.6.

### 3.4 Madhya Pradesh boards

| Abbrev | Full name | Established | Notes |
|---|---|---|---|
| MPBSE | Madhya Pradesh Board of Secondary Education | 1965 | Established under the M.P. Madhyamik Shiksha Adhiniyam, 1965. Conducts High School (X) and Higher Secondary (XII). Also known locally as "MP Board" / माध्यमिक शिक्षा मण्डल |
| MPSOS | Madhya Pradesh State Open School Education Board | 1996 | Open schooling at secondary and senior secondary level; syllabus mirrors MPBSE |

🔍 There is also a Madhya Pradesh Madrasa Board operating under the state minority welfare department. It is **not** seeded in v1; if a school selects "Other", the record goes to a super-admin review queue (§5.4).

### 3.5 Other state boards (seed the full list — required for Phase 2 and for out-of-state signups)

Seed all of the following so that an out-of-state signup does not hit a dead end. Only MPBSE, CBSE, CISCE and NIOS get examination content in v1.

| # | Abbrev | Full name | State/UT |
|---|---|---|---|
| 1 | UPMSP | Uttar Pradesh Madhyamik Shiksha Parishad | Uttar Pradesh |
| 2 | WBBSE | West Bengal Board of Secondary Education | West Bengal |
| 3 | WBCHSE | West Bengal Council of Higher Secondary Education | West Bengal |
| 4 | WBCROS | West Bengal Council of Rabindra Open Schooling | West Bengal |
| 5 | BSEB | Bihar School Examination Board | Bihar |
| 6 | BBOSE | Bihar Board of Open Schooling and Examination | Bihar |
| 7 | MSBSHSE | Maharashtra State Board of Secondary and Higher Secondary Education | Maharashtra |
| 8 | KSEEB | Karnataka Secondary Education Examination Board | Karnataka |
| 9 | DPUE | Department of Pre-University Education, Karnataka | Karnataka |
| 10 | DGE TN | Directorate of Government Examinations, Tamil Nadu | Tamil Nadu |
| 11 | BSEAP | Andhra Pradesh Board of Secondary Education | Andhra Pradesh |
| 12 | BIEAP | Board of Intermediate Education, Andhra Pradesh | Andhra Pradesh |
| 13 | APOSS | Andhra Pradesh Open School Society | Andhra Pradesh |
| 14 | SEBA | Board of Secondary Education, Assam | Assam |
| 15 | AHSEC | Assam Higher Secondary Education Council | Assam |
| 16 | CGBSE | Chhattisgarh Board of Secondary Education | Chhattisgarh |
| 17 | CGSOS | Chhattisgarh State Open School | Chhattisgarh |
| 18 | GBSHSE | Goa Board of Secondary and Higher Secondary Education | Goa |
| 19 | GSEB | Gujarat Secondary and Higher Secondary Education Board | Gujarat |
| 20 | HBSE | Haryana Board of School Education | Haryana |
| 21 | HPBOSE | Himachal Pradesh Board of School Education | Himachal Pradesh |
| 22 | JKBOSE | Jammu and Kashmir State Board of School Education | J&K |
| 23 | JAC | Jharkhand Academic Council | Jharkhand |
| 24 | KBPE | Kerala Board of Public Examination | Kerala |
| 25 | DGE Kerala | Directorate of General Education (Higher Secondary Wing) | Kerala |
| 26 | BVHSE | Board of Vocational Higher Secondary Education, Kerala | Kerala |
| 27 | BSEM | Board of Secondary Education, Manipur | Manipur |
| 28 | COHSEM | Council of Higher Secondary Education, Manipur | Manipur |
| 29 | MBOSE | Meghalaya Board of School Education | Meghalaya |
| 30 | MBSE | Mizoram Board of School Education | Mizoram |
| 31 | NBSE | Nagaland Board of School Education | Nagaland |
| 32 | BSE Odisha | Board of Secondary Education, Odisha | Odisha |
| 33 | CHSE Odisha | Council of Higher Secondary Education, Odisha | Odisha |
| 34 | PSEB | Punjab School Education Board | Punjab |
| 35 | RBSE | Board of Secondary Education, Rajasthan | Rajasthan |
| 36 | RSOS | Rajasthan State Open School | Rajasthan |
| 37 | BSE TS | Board of Secondary Education, Telangana State | Telangana |
| 38 | TSBIE | Telangana State Board of Intermediate Education | Telangana |
| 39 | TOSS | Telangana Open School Society | Telangana |
| 40 | TBSE | Tripura Board of Secondary Education | Tripura |
| 41 | UBSE | Uttarakhand Board of School Education | Uttarakhand |
| 42 | WBSCTVESD | West Bengal State Council of Technical & Vocational Education and Skill Development | West Bengal |

**Note on abbreviation collisions:** MBOSE (Meghalaya) and MBSE (Mizoram) are distinct; BSE TS, BSEB, BSEM and BSEAP all begin "BSE". The `boards.code` column **MUST** be unique and the UI **MUST** display `code — full_name — state` in every selector. Do not let a user disambiguate on abbreviation alone.

### 3.6 Seed data format

Ship this as `backend/app/seeds/boards.yaml`, loaded by an idempotent `seed_boards` management command. Each row:

```yaml
- code: MPBSE
  name_en: Madhya Pradesh Board of Secondary Education
  name_hi: माध्यमिक शिक्षा मण्डल, मध्य प्रदेश
  kind: STATE          # NATIONAL | STATE | INTERNATIONAL | OPEN_SCHOOLING
  state_code: MP       # null for national/international
  established_year: 1965
  official_url: https://mpbse.nic.in
  aliases: ["MP Board", "एमपी बोर्ड", "Madhyamik Shiksha Mandal"]
  certifications:
    - code: MPBSE_HS
      name_en: High School Certificate Examination
      class_level: 10
    - code: MPBSE_HSS
      name_en: Higher Secondary Certificate Examination
      class_level: 12
```

---

## 4. Master data: examinations

### 4.1 Examination taxonomy

```
Examination                      (stable identity: "JEE Main Paper 1")
  └── ExaminationEdition         (per academic year: "JEE Main Paper 1 — 2026")
        ├── PaperBlueprint       (sections, counts, marks, timing, languages)
        │     └── BlueprintSection ("Physics Section A", 20 Q, MCQ4, +4/-1)
        └── SyllabusTree         (Subject → Topic → Subtopic, versioned with the edition)
```

An `Examination` also carries:
- `scope`: `PAN_INDIA` | `STATE_MP` | `MULTI_STATE`
- `entry_class`: the class a candidate is in when they sit it (e.g. 5 for JNVST-VI, 8 for NMMS, 12 for NEET)
- `status`: `ACTIVE` | `DORMANT` | `DISCONTINUED`
- `mcq_fitness`: `PURE_MCQ` | `MCQ_PLUS_NUMERIC` | `MIXED` — controls whether we can fully model it in v1

### 4.2 Tier 1 — Pan-India examinations, high MP volume, Class 11–12

These are the anchor exams. Build content for these first.

#### 4.2.1 NEET (UG) — National Eligibility cum Entrance Test (Undergraduate)

| Attribute | Value |
|---|---|
| Conducting body | National Testing Agency (NTA) |
| Entry class | 12 (and repeaters) |
| Mode | Pen-and-paper, OMR |
| Total questions | 180, all compulsory |
| Structure | Physics 45, Chemistry 45, Botany 45, Zoology 45 |
| Duration | 180 minutes, no sectional timing |
| Total marks | 720 |
| Marking | +4 correct, −1 incorrect, 0 unattempted |
| Options per question | 4, single correct |
| Languages | 13, including Hindi and English |
| `mcq_fitness` | **PURE_MCQ** |
| Priority | **P0** |

**Why this is the flagship for us:** NEET is pure four-option MCQ administered on OMR. Our paper output and OMR sheet are a 1:1 match for the real exam experience. Nothing else in the catalogue fits the product this cleanly.

🔍 The 2025 cycle returned to the pre-COVID pattern: 180 compulsory questions replaced the earlier 200-question paper in which candidates attempted 180 by choosing 10 of 15 in each subject's Section B. Verify the current brochure before seeding — and note that the 2026 cycle had an exam cancellation and a re-test, which is a live reminder to check dates and pattern per cycle rather than assuming continuity.

**Subjects for syllabus tree:** Physics, Chemistry, Biology (with Botany and Zoology as first-level children, since the paper is scored by four blocks but the syllabus is published as three subjects).

#### 4.2.2 JEE Main — Paper 1 (B.E./B.Tech)

| Attribute | Value |
|---|---|
| Conducting body | NTA |
| Entry class | 12 (and repeaters) |
| Mode | Computer-based test |
| Total questions | 75, all compulsory |
| Structure | Physics / Chemistry / Mathematics, each: Section A = 20 MCQ, Section B = 5 numerical-value |
| Duration | 180 minutes |
| Total marks | 300 |
| Marking | +4 correct, −1 incorrect, both sections |
| Options per question | 4 (Section A); Section B is free numeric entry, rounded to nearest integer |
| Languages | 13, including Hindi and English |
| `mcq_fitness` | **MCQ_PLUS_NUMERIC** |
| Priority | **P0** |

**Implication for the data model:** JEE Main forces us to support a `NUMERIC` question type from day one — a question with no options and a correct answer expressed as a number plus a tolerance. Do not defer this; it is 20% of the paper. Our OMR generator must emit a numeric-entry grid (digit columns) for Section B, since our papers are administered on paper even though the real exam is CBT. See §12.4.

🔍 Section B changed in 2025: previously 10 questions with any 5 to be attempted and no negative marking; now 5 compulsory questions with negative marking. Also confirmed: no on-screen calculator is provided.

#### 4.2.3 CUET (UG) — Common University Entrance Test (Undergraduate)

| Attribute | Value |
|---|---|
| Conducting body | NTA |
| Entry class | 12 |
| Mode | Computer-based test |
| Structure | 3 sections: I Languages (13 languages), II Domain subjects (23), III General Test |
| Per paper | 50 compulsory MCQs, 60 minutes |
| Per-paper marks | 250 (5 marks per question) |
| Marking | +5 correct, −1 incorrect, 0 unattempted |
| Papers per candidate | Up to 5 |
| Total subject papers offered | 37 |
| Languages | 13 |
| `mcq_fitness` | **PURE_MCQ** |
| Priority | **P0** |

**Why it matters for MP:** CUET is the admission route to central universities and an increasing number of state universities, and its domain papers are based on the Class 12 NCERT syllabus — which means a CUET Chemistry practice paper doubles as CBSE Class 12 Chemistry revision. High content reuse.

🔍 The uniform 50-question / 60-minute / no-optional-questions structure came in with the 2025 cycle. Older CUET papers in our PYQ corpus (2022–2024) follow different section structures and question counts and must be tagged with their own edition blueprint, not force-fitted to the current one.

**Domain subjects to seed first (highest MP demand):** Physics, Chemistry, Mathematics/Applied Mathematics, Biology, Accountancy, Business Studies, Economics, History, Political Science, Geography, Psychology, Computer Science/Informatics Practices, plus Hindi and English from Section I and the General Test.

#### 4.2.4 CLAT (UG) — Common Law Admission Test

| Attribute | Value |
|---|---|
| Conducting body | Consortium of National Law Universities |
| Entry class | 12 |
| Mode | Pen-and-paper, OMR |
| Total questions | 120, all passage-based |
| Duration | 120 minutes |
| Total marks | 120 |
| Marking | +1 correct, −0.25 incorrect |
| Sections (approx. counts) | English Language 22–26; Current Affairs incl. GK 28–32; Legal Reasoning 28–32; Logical Reasoning 22–26; Quantitative Techniques 10–14 |
| Language | English only |
| `mcq_fitness` | **PURE_MCQ** |
| Priority | **P1** |

**Modelling note:** CLAT is entirely comprehension-passage driven — a 450–500 word passage carries 5–6 questions. This requires a `question_group` entity (a shared stimulus with multiple child questions) that must be selected and printed as an atomic unit. Build `question_group` into the schema now even though only CLAT uses it in v1; NMMS SAT and CUET English will use it too. See §5.7.

**Language note:** CLAT is English-medium only. The bilingual requirement does **not** apply. The schema must permit an examination to declare `supported_locales: ["en"]` and the paper generator must not attempt a Hindi rendering.

#### 4.2.5 NDA & NA — National Defence Academy and Naval Academy Examination

| Attribute | Value |
|---|---|
| Conducting body | Union Public Service Commission (UPSC) |
| Entry class | 12 |
| Mode | Pen-and-paper, OMR |
| Papers | Paper I Mathematics; Paper II General Ability Test (GAT) |
| Paper I 🔍 | 120 questions, 300 marks, 150 minutes |
| Paper II 🔍 | 150 questions, 600 marks, 150 minutes; GAT = English + General Knowledge |
| Marking 🔍 | Negative marking of one-third of the marks assigned to the question |
| Languages | Hindi and English (except the English section) |
| `mcq_fitness` | **PURE_MCQ** |
| Priority | **P2** |

🔍 All NDA figures above are seeded `UNVERIFIED`. Confirm against the current UPSC NDA & NA examination notice before enabling. UPSC notices are the only acceptable source.

#### 4.2.6 JEE Advanced — deliberately deferred

JEE Advanced uses single-correct MCQ, **multiple-correct** MCQ with partial marking, integer/decimal answer types, and matching-list questions, with a marking scheme that changes year to year. Partial-credit multiple-correct questions do not fit a standard OMR-and-key model without substantial extra work.

**Decision: out of scope for v1.** Seed the `Examination` row with `status = DORMANT` and `mcq_fitness = MIXED` so the catalogue is honest, but do not build content. Revisit in v2 with a proper multi-correct + partial-marking item model.

### 4.3 Tier 2 — Madhya Pradesh state examinations

#### 4.3.1 MPBSE Class 12 (Higher Secondary) — objective component

| Attribute | Value |
|---|---|
| Conducting body | Madhya Pradesh Board of Secondary Education (MPBSE) |
| Entry class | 12 |
| Mode | Pen-and-paper |
| Objective component 🔍 | 20 objective questions of 1 mark each, compulsory, within the theory paper |
| Theory paper marks 🔍 | 80 for most subjects; Mathematics is 100 marks theory only |
| Practical / internal 🔍 | 20 marks (practical for science subjects; internal assessment for commerce and humanities) |
| Overall question design 🔍 | Approximately 40% objective, 40% subjective, 20% analytical |
| Duration | 3 hours (full paper) |
| Languages | Hindi and English medium |
| Scale | ~7 lakh candidates per year |
| `mcq_fitness` | **MIXED** (we serve only the objective block) |
| Priority | **P0** |

**This is the single highest-volume opportunity in MP** and the one most aligned with Pratibha Mandir's existing Hindi-medium production. But note the product shape is different: we are not generating a whole MPBSE paper, we are generating the *objective section* — or, more usefully, a **20-question objective practice test** in the exact style and weightage of the board's objective block.

**Design implication:** introduce a `paper_purpose` concept alongside `examination`. A teacher generating an "MPBSE Class 12 Chemistry" paper picks a purpose:
- `MOCK_OFFICIAL` — mirrors the official objective block exactly (20 Q, 1 mark each)
- `PRACTICE_SET` — teacher-defined count (e.g. 40 Q on Electrochemistry and Chemical Kinetics)
- `CHAPTER_TEST` — scoped to one or more syllabus nodes

For an exam like NEET, `MOCK_OFFICIAL` and `PRACTICE_SET` both make sense. For MPBSE, `PRACTICE_SET` will be the dominant mode. The blueprint engine must handle both.

🔍 MPBSE publishes a subject-wise blueprint (chapter-wise marks distribution) each session on `mpbse.nic.in`. This is the authoritative source for topic weightage and **must** be fetched per subject per year by the ToC Refresh Agent. Do not derive weightage from coaching sites.

#### 4.3.2 MPBSE Class 10 (High School) — objective component

| Attribute | Value |
|---|---|
| Conducting body | MPBSE |
| Entry class | 10 |
| Theory / internal split 🔍 | 75 theory + 25 internal (some sources say 80 + 20 for non-practical subjects — verify per subject) |
| Question design 🔍 | ~40% objective, 40% subjective, 20% analytical |
| Subjects | Two languages + Mathematics, Science, Social Science |
| Scale | ~5 lakh candidates per year |
| `mcq_fitness` | **MIXED** |
| Priority | **P0** |

🔍 The 75+25 vs 80+20 split appears inconsistently across sources and may vary by whether the subject has a practical component. Resolve from the official MPBSE blueprint PDF per subject. Log the resolution in `edition_source_conflicts`.

#### 4.3.3 MP PPT — Madhya Pradesh Pre Polytechnic Test

| Attribute | Value |
|---|---|
| Conducting body | Madhya Pradesh Employees Selection Board (MPESB / MP ESB) — formerly MP Vyapam / MP PEB |
| Entry class | 10 |
| Purpose | Admission to first-year diploma programmes in polytechnic institutions in MP |
| Subjects | Mathematics, Physics, Chemistry — at Class 10 level |
| Question type | Objective |
| Languages | Hindi and English |
| Official portal | `esb.mp.gov.in` |
| `mcq_fitness` | **PURE_MCQ** 🔍 |
| Priority | **P1** |

🔍 Exact question count, duration, marks and negative-marking policy must be taken from the MPESB rule book for the relevant year. The rule book is the authoritative document for all MPESB exams.

#### 4.3.4 MP PAT — Madhya Pradesh Pre Agriculture Test

| Attribute | Value |
|---|---|
| Conducting body | MPESB |
| Entry class | 12 |
| Purpose | Admission to B.Sc. (Hons) Agriculture, Horticulture, Forestry and allied programmes at RVSKVV Gwalior and JNKVV Jabalpur |
| Total questions | 200 MCQ |
| Structure | Group A: Physics, Chemistry, Mathematics · Group B: Physics, Chemistry, Biology/Agriculture (candidate may take one group or both) |
| Level | Class 12 |
| Duration | 3 hours |
| Mode | Computer-based test |
| Negative marking | None |
| Languages | Bilingual (Hindi and English) |
| Official portal | `esb.mp.gov.in` |
| `mcq_fitness` | **PURE_MCQ** |
| Priority | **P1** |

**Note the group structure.** A candidate selects Group A, Group B, or both. This means the blueprint must support *candidate-selected variants* of the same edition — the same paper identity produces different question sets depending on the group. Model as sibling `PaperBlueprint` rows under one edition with a `variant_code` (`GROUP_A`, `GROUP_B`).

**No negative marking** is significant for the Exam Creator: instructions text, difficulty targeting and the OMR sheet all differ from a negatively-marked exam. Do not hardcode negative marking as universal.

#### 4.3.5 MPSOS — MP State Open School

Syllabus mirrors MPBSE. Model as a separate `Examination` referencing the same syllabus tree via a `syllabus_alias` rather than duplicating nodes. Priority **P2**.

### 4.4 Tier 3 — Selection and scholarship examinations, Class 5–9

These are strategically important: they are almost all pure OMR MCQ, they are heavily Hindi-medium in MP, and no serious digital question bank serves them well.

#### 4.4.1 NMMS — National Means-cum-Merit Scholarship Examination

| Attribute | Value |
|---|---|
| Conducting body | State SCERT / Rajya Shiksha Kendra (MP) under a centrally sponsored scheme |
| Entry class | 8 |
| Papers | MAT (Mental Ability Test) and SAT (Scholastic Aptitude Test) |
| MAT | 90 MCQ, 90 marks, 90 minutes — verbal and non-verbal reasoning: analogy, classification, numerical series, pattern perception, hidden figures |
| SAT | 90 MCQ, 90 marks, 90 minutes — Science, Social Studies, Mathematics as taught in Classes 7 and 8 |
| Marking | 1 mark per correct answer, **no negative marking** |
| Mode | Pen-and-paper, OMR |
| Qualifying | 🔍 Typically 40% in each paper separately (relaxed for SC/ST) — varies by state notification |
| Languages | Hindi, English, and other state media |
| Awards | ~100,000 scholarships nationally per year, distributed state-wise |
| `mcq_fitness` | **PURE_MCQ** |
| Priority | **P0** |

**Strongest product-market fit in Tier 3.** Pure MCQ, OMR-administered, Hindi-medium, Class 8, MP-relevant, high parent motivation, and almost entirely served today by print practice-set books. Our OMR sheet is directly usable.

🔍 SAT subject splits vary by state notification. One state publishes Science 35 / Social Science 35 / Mathematics 20. **Do not assume MP uses this split** — fetch the MP Rajya Shiksha Kendra notification. Seed as `UNVERIFIED`.

#### 4.4.2 JNVST — Jawahar Navodaya Vidyalaya Selection Test, Class 6

| Attribute | Value |
|---|---|
| Conducting body | Navodaya Vidyalaya Samiti (NVS), Ministry of Education |
| Entry class | 5 |
| Total questions | 80 |
| Total marks | 100 (1.25 marks per question) |
| Duration | 120 minutes, **with per-section time limits that cannot be pooled** |
| Section 1 🔍 | Mental Ability Test + EVS — 40 questions (20 MAT + 20 EVS), 50 marks, 60 minutes |
| Section 2 | Arithmetic — 20 questions, 25 marks, 30 minutes |
| Section 3 | Language — 20 questions, 25 marks, 30 minutes |
| Negative marking | None |
| Languages | 29+ languages including Hindi |
| Syllabus basis | NCERT Class 4 and 5 |
| `mcq_fitness` | **PURE_MCQ** |
| Priority | **P1** |

🔍 **Pattern change alert.** The addition of an EVS component to Section 1 is recent. Older sources describe Section 1 as "Mental Ability Test, 40 questions, 50 marks" with no EVS. Any PYQ ingested from before the change must be tagged to the older edition. Fetch the current NVS Prospectus — it is the authoritative source and is published annually at `navodaya.gov.in`.

**Design implication — sectional timing.** JNVST enforces per-section time limits. Our generated paper and its instruction block must communicate this. Add `section_duration_minutes` to `BlueprintSection` (nullable; null means pooled timing).

**Design implication — fractional marks.** 1.25 marks per question means marks must be `NUMERIC(6,2)`, not integer. Also note the qualifying rule is sectional (🔍 reported as 14 marks in Section 1, 7 in Section 2, 7 in Section 3, all three required), which the answer key document should surface.

#### 4.4.3 JNVST Class 9 (lateral entry)

🔍 Reported as 100 questions / 100 marks / 2.5 hours across English, Hindi, Mathematics and Science. **All figures unverified.** Seed `UNVERIFIED`, priority **P2**.

#### 4.4.4 AISSEE — All India Sainik Schools Entrance Examination

| Attribute | Value |
|---|---|
| Conducting body | National Testing Agency (NTA), for Sainik Schools |
| Entry classes | 6 and 9 |
| Mode | Pen-and-paper, OMR |
| Class 6 subjects 🔍 | Language, Mathematics, Intelligence, General Knowledge |
| Class 9 subjects 🔍 | Mathematics, Intelligence, English, General Science, Social Science |
| Languages | Multiple including Hindi |
| `mcq_fitness` | **PURE_MCQ** 🔍 |
| Priority | **P2** |

🔍 **All question counts, marks and durations for AISSEE are unverified.** Do not seed numbers from this document. Fetch the NTA AISSEE Information Bulletin.

#### 4.4.5 RMS CET — Rashtriya Military School Common Entrance Test

Classes 6 and 9. 🔍 Entirely unverified. Priority **P3**. Seed the `Examination` row only.

#### 4.4.6 SOF Olympiads — NSO, IMO, IEO, NCO, IGKO

| Attribute | Value |
|---|---|
| Conducting body | Science Olympiad Foundation (SOF) |
| Entry classes | 1–12 |
| Level 1 format | Objective MCQ on OMR, conducted in-school during school hours, 60 minutes |
| Classes 1–4 | 35 questions, 40 marks |
| Classes 5–12 | 50 questions, 60 marks |
| Section structure (IMO) | S1 Logical Reasoning · S2 Mathematical Reasoning · S3 Everyday Mathematics · S4 Achievers Section |
| Section structure (NSO, Cl. 11–12) 🔍 | Physics & Chemistry 25 Q (1 mark) · Mathematics or Biology 20 Q (1 mark) · Achievers 5 Q (3 marks) = 50 Q / 60 marks |
| Section structure (NSO, Cl. 5–8) 🔍 | Logical Reasoning 10 (1 mark) · Science 35 (1 mark) · Achievers 5 (3 marks) = 50 Q / 60 marks |
| Section structure (NSO, Cl. 1–4) 🔍 | Logical Reasoning 5 (1 mark) · Science 25 (1 mark) · Achievers 5 (2 marks) = 35 Q / 40 marks |
| Achievers weighting | ×2 marks for Classes 1–4, ×3 marks from Class 5 |
| Negative marking | None |
| Language | English |
| Level 2 | Classes 3–12 only; top performers from Level 1 |
| `mcq_fitness` | **PURE_MCQ** |
| Priority | **P1** for IMO and NSO; **P2** for IEO, NCO, IGKO |

**Why P1:** Olympiads are administered *in the school*, by the school, which means the school admin persona is the buyer, the format is OMR MCQ, and schools already run internal practice rounds. This is the cleanest school-level (as opposed to teacher-level) sale in the catalogue.

**Design implication — differential marks within a paper.** The Achievers Section carries 2× or 3× marks. `BlueprintSection.marks_per_question` must be per-section, not per-paper. Already accounted for in the schema (§5.6).

**Note:** SOF papers are English-medium. `supported_locales: ["en"]`.

#### 4.4.7 NTSE — National Talent Search Examination (DORMANT)

| Attribute | Value |
|---|---|
| Conducting body | NCERT (Stage 2); state SCERTs (Stage 1) |
| Entry class | 10 |
| Status | **DORMANT** |

The National Talent Search Scheme was approved through 31 March 2021. NCERT subsequently notified that further implementation of the scheme in its present form had not been approved and was stalled until further orders, and the examination has not been conducted since. Stage 1 for the 2021–22 cycle was postponed and never held.

**Decision:** seed with `status = DORMANT`. Keep the archived Stage 1 and Stage 2 papers in the question bank — they are excellent MAT/SAT practice material for Class 10 students and can be surfaced under a "Legacy NTSE practice" label. Do **not** advertise NTSE as a live examination. The Exam Creator must display a dormancy notice when a dormant examination is selected. If NCERT revives the scheme, flip `status` to `ACTIVE` and run the ToC Refresh Agent.

This is a good example of why `status` exists as a column and why the annual refresh job must be able to *retire* an examination, not only update it.

### 4.5 Examination priority matrix — what to build first

| Priority | Examinations | Rationale |
|---|---|---|
| **P0** | NEET (UG), JEE Main Paper 1, CUET (UG), MPBSE Class 12, MPBSE Class 10, NMMS | Highest MP volume; anchors both the Hindi-medium and the competitive-exam value propositions; NEET and NMMS are pure OMR MCQ and demo perfectly |
| **P1** | CLAT, MP PPT, MP PAT, JNVST Class 6, SOF IMO, SOF NSO | Strong fit, moderate volume, or school-level (rather than teacher-level) buyers |
| **P2** | NDA & NA, JNVST Class 9, AISSEE, MPSOS, SOF IEO/NCO/IGKO | Long tail; enable after the pipeline is proven |
| **P3 / deferred** | JEE Advanced, RMS CET, IAPT NSEs (NSEP/NSEC/NSEB/NSEA/NSEJS), NSTSE, Silverzone, Vidyarthi Vigyan Manthan | Complex item types, or unverified, or low volume |

### 4.6 Examinations explicitly excluded from v1

- **International board assessments (IB, CAIE, Pearson).** Included as *board affiliations* so international schools can sign up and use the platform for their own internal MCQ tests, but no examination content is seeded. IB and CAIE assessment materials are tightly licensed and the syllabus documents are not freely redistributable.
- **Teacher recruitment exams (MP TET, CTET, MPESB teacher recruitment).** Wrong audience — the candidate is the teacher, not the student.
- **Post-Class-12 entrance exams that are not taken from school** (state PET/PMT variants for graduates, MCA/MBA entrances).
- **Any examination whose question papers are not lawfully reproducible.** See §14.5.

### 4.7 Seed data format

Ship as `backend/app/seeds/examinations/<code>.yaml`:

```yaml
code: NEET_UG
name_en: NEET (UG) — National Eligibility cum Entrance Test (Undergraduate)
name_hi: नीट (यूजी) — राष्ट्रीय पात्रता सह प्रवेश परीक्षा (स्नातक)
conducting_body: National Testing Agency (NTA)
official_url: https://neet.nta.nic.in
scope: PAN_INDIA
entry_class: 12
status: ACTIVE
mcq_fitness: PURE_MCQ
supported_locales: [en, hi]
priority: P0
editions:
  - year: 2026
    verification_state: UNVERIFIED     # flip only after human review of the brochure
    source_url: null                   # MUST be the official information bulletin PDF
    mode: OFFLINE_OMR
    blueprints:
      - variant_code: DEFAULT
        duration_minutes: 180
        sectional_timing: false
        total_marks: 720
        sections:
          - code: PHY
            name_en: Physics
            question_count: 45
            question_type: MCQ_SINGLE
            options_count: 4
            marks_per_question: 4
            negative_marks: 1
          - code: CHE
            name_en: Chemistry
            question_count: 45
            question_type: MCQ_SINGLE
            options_count: 4
            marks_per_question: 4
            negative_marks: 1
          - code: BOT
            name_en: Botany
            question_count: 45
            question_type: MCQ_SINGLE
            options_count: 4
            marks_per_question: 4
            negative_marks: 1
          - code: ZOO
            name_en: Zoology
            question_count: 45
            question_type: MCQ_SINGLE
            options_count: 4
            marks_per_question: 4
            negative_marks: 1
```

---

## 4.8 Subjects

The subject taxonomy is shared across boards and examinations, and is seeded from `backend/app/seeds/subjects.yaml`. The full list is in Appendix C of this document.

Three distinctions matter and are easy to get wrong:

1. **`SCIENCE` (Classes 6–10) is not `PHYSICS` + `CHEMISTRY` + `BIOLOGY` (Classes 11–12).** They are separate subjects with separate syllabus trees. An MPBSE Class 10 Science question is not a Physics question. Do not merge them.
2. **`BIOLOGY` has `BOTANY` and `ZOOLOGY` as children.** NEET scores four blocks (Physics, Chemistry, Botany, Zoology) but the syllabus is published as three subjects. The tree reflects the syllabus; the blueprint reflects the scoring.
3. **Competitive-only subjects** — Mental Ability, Legal Reasoning, Everyday Mathematics, Intelligence, General Test — have no class-level teaching equivalent. They carry `is_teachable = FALSE` so they never appear in the teacher-assignment picker (document 3, §7.4), but they must exist so competitive papers can be structured.

---

## 4.9 Topics and sub-topics — the syllabus tree

Every examination edition owns a versioned tree: **Subject → Topic → Sub-topic**, arbitrary depth, stored as `syllabus_nodes` with an `ltree` materialised path (schema in document 3, §5.6).

**Why the tree is per-edition and not global.** JNVST Class 6 restructured its first section to fold Environmental Studies in with Mental Ability. A question bank mapped to the previous three-section structure is now mis-mapped. Because every edition owns its own tree and every generated paper pins an `edition_id`, that change is a new edition rather than a destructive migration, and papers generated last year still reproduce correctly.

**Weightage — two different numbers, never conflated.**

| Field | Source | Shown to users as |
|---|---|---|
| `weightage_pct` | Published official blueprint | "Board blueprint" |
| `empirical_weightage_pct` | Computed from 10 years of past papers | "Observed in past papers" |

MPBSE publishes chapter-wise marks distribution per subject per session, so `weightage_pct` is available and authoritative for board exams. The NTA does not publish weightage for NEET or JEE Main, so only the empirical figure exists there. **Never present a derived number as official.** The distinction feeds the allocation algorithm in document 4, §10.2, and the wizard in document 3, §7.5.

**Node availability drives the UI.** The `syllabus_node_availability` materialised view (document 3, §5.16) gives per-node verified counts by difficulty and by locale, so a teacher selecting "Rotational Motion" sees *"84 questions available"* rather than discovering a shortfall after paying.

---

## 4.10 Authentic sources — how to obtain and maintain all of the above

This is the operational heart of the document. Content is only as good as its source, and sources move.

### Source hierarchy

Strict, non-negotiable, and enforced by the web-fetch allow-list (document 3, §14.5):

1. **The conducting body's own site.** Information bulletins, prospectuses, rule books, blueprints, syllabus PDFs, official answer keys and challenge-resolution documents.
2. **Official answer keys and revision notices** published by the same body.
3. **Reputable publishers with an explicit licence** or public-domain status.
4. **Everything else** — usable only as corroboration for an answer, never as the authoritative text of a question or the authoritative structure of a syllabus.

An aggregator or coaching site is category 4 *at best*. Their compiled and edited version of a paper carries their editorial layer; their summary of an exam pattern is frequently stale, as several of the 🔍 markers in §4 attest.

### Primary source per examination

| Examination | Authoritative document | Where |
|---|---|---|
| NEET (UG) | Information Bulletin, Syllabus | `neet.nta.nic.in`, `nta.ac.in` |
| JEE Main | Information Bulletin, Syllabus | `jeemain.nta.ac.in` |
| CUET (UG) | Information Bulletin, subject syllabi | `cuet.nta.nic.in` |
| AISSEE | Information Bulletin | `exams.nta.ac.in/AISSEE` |
| NDA & NA | UPSC Examination Notice | `upsc.gov.in` |
| CLAT | Consortium notification and sample papers | `consortiumofnlus.ac.in` |
| MPBSE Class 10 / 12 | **Blueprint PDF, published per subject per session**, plus the time table | `mpbse.nic.in` |
| MP PPT, MP PAT | MPESB **rule book** for the year | `esb.mp.gov.in` |
| NMMS | MP Rajya Shiksha Kendra / SCERT state notification | State education portal |
| JNVST | **NVS Prospectus**, published annually | `navodaya.gov.in` |
| SOF Olympiads | Syllabus and sample papers | `sofworld.org` |
| NTSE (dormant) | NCERT notices | `ncert.nic.in` |
| Board list | COBSE recognised-boards list; Ministry of Education board listing | — |

**Note the shape differences.** MPBSE publishes *one blueprint PDF per subject*, so its locator config sets `per_subject: true`. MPESB publishes a single rule book covering pattern, syllabus and marking. NVS publishes a prospectus that changes structure between years. There is no universal parser; each examination gets a locator profile.

### 10.4 ToC Refresh Agent — keeping all of the above current

**Goal (requirement #9):** annually refresh the authentic table of contents per examination, from the true source, under super-admin control.

**Never auto-applies.** Produces a diff for approval.

```
1. LOCATE   → find the current official syllabus/prospectus/rule-book/blueprint
              document for (examination, year). Uses a per-examination
              `source_locator` config: a base URL, a link pattern, and a
              document-type signature.
2. FETCH    → download; checksum; if checksum == last known, exit "no change"
3. PARSE    → extract the syllabus hierarchy and, where published, weightage
4. DIFF     → structural diff against the current edition's syllabus_nodes:
              ADDED / REMOVED / RENAMED / MOVED / REWEIGHTED
5. IMPACT   → for each REMOVED or MOVED node, count affected questions
6. PROPOSE  → write a draft examination_edition (UNVERIFIED) + a diff document
7. NOTIFY   → super admin
8. APPROVE  → human approves; the new edition becomes ACTIVE and supersedes
              the old one; a remapping job moves questions to new node ids
```

**The `source_locator` config per examination** is the thing that makes this maintainable:

```yaml
NEET_UG:
  source_locator:
    base_url: https://neet.nta.nic.in
    strategy: LINK_PATTERN
    link_patterns:
      - "Information Bulletin"
      - "Syllabus"
    document_type: PDF
    expected_sections: ["Physics", "Chemistry", "Botany", "Zoology"]
    fallback_urls:
      - https://nta.ac.in
MPBSE_XII:
  source_locator:
    base_url: https://mpbse.nic.in
    strategy: LINK_PATTERN
    link_patterns: ["Blueprint", "ब्लूप्रिंट", "Syllabus"]
    per_subject: true          # MPBSE publishes one blueprint PDF per subject
    document_type: PDF
```

**Scheduling.** A Celery Beat job runs monthly per active examination (cheap — usually exits at the checksum step), plus an on-demand trigger. Monthly rather than annual because boards publish revisions mid-cycle, and because JNVST's Section 1 restructure and JEE Main's Section B change both arrived as mid-cycle notifications.

**Question remapping on approval.** When a node is `RENAMED` or `MOVED`, questions follow automatically. When a node is `REMOVED`, affected questions are set `is_active = FALSE` with `retired_reason = 'SYLLABUS_REMOVED_2027'` — **not deleted**. They remain valid for papers targeting the older edition, which is exactly why `generated_papers` pins an `edition_id`.

**Conflict logging.** When the parsed structure disagrees with a secondary source, write to `edition_source_conflicts` and surface it in the approval UI. Never silently pick one.

---

## Appendix B — Source references for §3 and §4

Every figure in the examination catalogue must be re-confirmed against the primary source before an edition is approved. Primary sources by examination:

| Examination | Primary source |
|---|---|
| NEET (UG), JEE Main, CUET (UG), AISSEE | NTA information bulletins — `nta.ac.in` and the exam-specific portals |
| CLAT | Consortium of National Law Universities — `consortiumofnlus.ac.in` |
| NDA & NA | UPSC examination notice |
| MPBSE Class 10 / 12 | MPBSE blueprints and time tables — `mpbse.nic.in` (per subject, per session) |
| MP PPT, MP PAT | MPESB rule books — `esb.mp.gov.in` |
| NMMS | MP Rajya Shiksha Kendra / SCERT notification |
| JNVST | NVS Prospectus — `navodaya.gov.in` |
| SOF Olympiads | `sofworld.org` |
| NTSE (dormant) | NCERT notices — `ncert.nic.in` |
| Board list | COBSE recognised-boards list; Ministry of Education board listing |

The figures in §4 were compiled from public reporting current as of August 2026 and cross-checked across multiple secondary sources where an official source was not directly retrievable. **Treat every one of them as a hypothesis to be confirmed, not a fact to be relied on.** That is the entire point of `verification_state` and the ToC Refresh Agent.

---

---

## Appendix C — Subject taxonomy seed

`backend/app/seeds/subjects.yaml`. Codes are stable identifiers; never renumber. `stream` is nullable and used only for filtering in the UI.

**Languages**

| Code | English | Hindi | Classes |
|---|---|---|---|
| `HINDI` | Hindi | हिन्दी | 1–12 |
| `ENGLISH` | English | अंग्रेज़ी | 1–12 |
| `SANSKRIT` | Sanskrit | संस्कृत | 6–12 |
| `URDU` | Urdu | उर्दू | 1–12 |
| `MARATHI` | Marathi | मराठी | 1–12 |

**Primary and middle**

| Code | English | Hindi | Classes |
|---|---|---|---|
| `EVS` | Environmental Studies | पर्यावरण अध्ययन | 1–5 |
| `MATHEMATICS` | Mathematics | गणित | 1–12 |
| `SCIENCE` | Science | विज्ञान | 6–10 |
| `SOCIAL_SCIENCE` | Social Science | सामाजिक विज्ञान | 6–10 |

**Senior secondary — Science**

| Code | English | Hindi | Stream |
|---|---|---|---|
| `PHYSICS` | Physics | भौतिक विज्ञान | SCIENCE |
| `CHEMISTRY` | Chemistry | रसायन विज्ञान | SCIENCE |
| `BIOLOGY` | Biology | जीव विज्ञान | SCIENCE |
| `BOTANY` | Botany | वनस्पति विज्ञान | SCIENCE |
| `ZOOLOGY` | Zoology | प्राणि विज्ञान | SCIENCE |
| `APPLIED_MATHEMATICS` | Applied Mathematics | अनुप्रयुक्त गणित | SCIENCE |
| `COMPUTER_SCIENCE` | Computer Science | कंप्यूटर विज्ञान | SCIENCE |
| `INFORMATICS_PRACTICES` | Informatics Practices | सूचना विज्ञान अभ्यास | SCIENCE |
| `BIOTECHNOLOGY` | Biotechnology | जैव प्रौद्योगिकी | SCIENCE |

**Senior secondary — Commerce**

| Code | English | Hindi |
|---|---|---|
| `ACCOUNTANCY` | Accountancy | लेखाशास्त्र |
| `BUSINESS_STUDIES` | Business Studies | व्यवसाय अध्ययन |
| `ECONOMICS` | Economics | अर्थशास्त्र |
| `ENTREPRENEURSHIP` | Entrepreneurship | उद्यमिता |

**Senior secondary — Humanities**

| Code | English | Hindi |
|---|---|---|
| `HISTORY` | History | इतिहास |
| `POLITICAL_SCIENCE` | Political Science | राजनीति विज्ञान |
| `GEOGRAPHY` | Geography | भूगोल |
| `SOCIOLOGY` | Sociology | समाजशास्त्र |
| `PSYCHOLOGY` | Psychology | मनोविज्ञान |
| `PHILOSOPHY` | Philosophy | दर्शनशास्त्र |
| `HOME_SCIENCE` | Home Science | गृह विज्ञान |
| `PHYSICAL_EDUCATION` | Physical Education | शारीरिक शिक्षा |
| `FINE_ARTS` | Fine Arts | कला |

**MP Board specific**

| Code | English | Hindi | Note |
|---|---|---|---|
| `AGRICULTURE` | Agriculture | कृषि | MPBSE XII and MP PAT Group B |
| `CROP_PRODUCTION` | Crop Production and Horticulture | फसल उत्पादन एवं उद्यान विज्ञान | MPBSE vocational |
| `ANIMAL_HUSBANDRY` | Animal Husbandry | पशुपालन | MPBSE vocational |
| `NSQF_VOCATIONAL` | NSQF Vocational | एनएसक्यूएफ व्यावसायिक | Parent node; trades as children |

**Competitive-exam-only subjects** — these have no class-level teaching equivalent and exist so competitive papers can be structured. They are hidden from the teacher-assignment picker (`is_teachable = FALSE`).

| Code | English | Hindi | Used by |
|---|---|---|---|
| `MENTAL_ABILITY` | Mental Ability | मानसिक योग्यता | NMMS MAT, JNVST, AISSEE, SOF |
| `LOGICAL_REASONING` | Logical Reasoning | तार्किक विचारण | SOF, CLAT |
| `EVERYDAY_MATHEMATICS` | Everyday Mathematics | दैनिक गणित | SOF IMO |
| `GENERAL_KNOWLEDGE` | General Knowledge | सामान्य ज्ञान | AISSEE, NDA GAT, SOF IGKO |
| `CURRENT_AFFAIRS` | Current Affairs | समसामयिकी | CLAT |
| `LEGAL_REASONING` | Legal Reasoning | विधिक विचारण | CLAT |
| `QUANTITATIVE_TECHNIQUES` | Quantitative Techniques | मात्रात्मक तकनीक | CLAT |
| `GENERAL_TEST` | General Test | सामान्य परीक्षण | CUET Section III |
| `ARITHMETIC` | Arithmetic | अंकगणित | JNVST |
| `INTELLIGENCE` | Intelligence | बुद्धिमत्ता | AISSEE, RMS CET |

**Naming caution.** `SCIENCE` (Classes 6–10) and `PHYSICS`/`CHEMISTRY`/`BIOLOGY` (11–12) are distinct subjects, not the same subject at different levels. An MPBSE Class 10 Science question is not a Physics question. Do not merge them; the syllabus trees differ and so does the teacher who sets the paper.

---

*Document 2 of 5. Next: `03-technical.md`.*
