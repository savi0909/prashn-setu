# Prashn Setu — Documentation Set

Objective question paper portal for Madhya Pradesh schools and coaching institutes.
Owner: Pratibha Mandir. Implementing engineer: Abhishek Mittal.

**Stack at a glance:** React + TypeScript · FastAPI · PostgreSQL + pgvector · Celery/Redis · application tier on **E2E Networks Cloud** (Indian regions) · inference on **Gemma 4 31B Instruct, self-hosted on DeepMindSecure.AI GPUs** · MSG91 for SMS/email · Razorpay for payments.

## The five documents

| # | File | Read it when you need to know… | Lines |
|---|---|---|---|
| 1 | [`01-problem-actors-usecases.md`](01-problem-actors-usecases.md) | What is being built, for whom, in what order, and what is still undecided | ~320 |
| 2 | [`02-examinations-and-syllabus.md`](02-examinations-and-syllabus.md) | Which examinations and boards matter in MP, what is inside them, and where authentic data comes from | ~790 |
| 3 | [`03-technical.md`](03-technical.md) | Database schema, APIs, web pages, notifications, payments, testing, infrastructure | ~2290 |
| 4 | [`04-question-bank-agent.md`](04-question-bank-agent.md) | How the corpus is generated, verified without an answer key, made bilingual, and explained three ways | ~750 |
| 5 | [`05-exam-creator-agent.md`](05-exam-creator-agent.md) | How a teacher's request becomes a printable branded paper with an OMR sheet | ~280 |

## Cross-references

Section numbers are preserved from the original combined plan, so a reference like §9.7 means the same thing in every file. Where a referenced section lives elsewhere, the map at the top of each document says which file to open.

## Reading order

- **New to the project** → 1, then 2, then whichever of 3/4/5 matches your work.
- **Starting to build** → 1 §15.4 (build order), then 3.
- **Working on content** → 2, then 4.
- **Product or commercial questions** → 1 §17 (decision log) and §18 (risks).

## Using with Claude Code

Commit all six files under `docs/`. Create `CLAUDE.md` at repo root with the stack summary (3 §2.3), repo layout (3 §16.1), coding conventions (3 §16.2), and a pointer here.

Open each session by naming the document and sections:

> *"Read `docs/03-technical.md` §5.3 through §5.5 and §6.2. Implement Milestone 1 from `docs/01-problem-actors-usecases.md` §15.4. Write tests first."*

Do not paste all five documents into a prompt. Naming sections works better and costs less.

## Two things to start before writing any code

1. **DLT entity and template registration** with MSG91 — external lead time in days to weeks, and blocked SMS will stall onboarding. See 3 §8.1.
2. **E2E Cloud and MSG91 account setup.**
3. **DeepMindSecure.AI due diligence (DEC-18)** — GPU location, private connectivity, egress pricing, SLA and model-revision control. Data residency in particular feeds the DPDP posture. See 4 §9.1.
