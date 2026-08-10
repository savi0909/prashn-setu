> **STATUS — PROPOSAL, NOT YET ACCEPTED.** Added verbatim on 11 August 2026 at
> the owner's request. It has not been reconciled with the document set and it
> conflicts with four things already decided. Do not implement from it until
> those are resolved:
>
> 1. **It introduces Neo4j as a second database.** The stack summary in
>    `CLAUDE.md` and document 3 §2.3 specify PostgreSQL + pgvector + ltree only.
>    A knowledge graph alongside the transactional store is a significant
>    architectural decision and needs a DEC entry and an ADR before any
>    `docker-compose` change.
> 2. **It re-specifies M0, which is already complete and merged** — compose,
>    Alembic, the FastAPI skeleton, health and readiness endpoints, CI, and
>    pre-commit all landed in commit `1f41834`.
> 3. **It reads `docs/IMPLEMENTATION_PLAN.md`, which no longer exists.** That was
>    the superseded v1.0 combined file, deleted under ADR 0002. The
>    specification of record is `docs/00-README.md` through `05-…`, plus
>    `06-logical-domain-model.md`.
> 4. **Its §38 builds the frontend shell**, which ADR 0001 defers — the
>    corpus-first order runs §5.5 → §5.6 → §5.7 with the frontend deferred, not
>    cancelled.
>
> Its `DEC-M0-01`…`DEC-M0-05` numbering is also separate from the decision
> register in document 1 §17, which currently runs to DEC-25.
>
> **Implementation remains frozen** until `docs/06-logical-domain-model.md`
> reaches v1.0 — see its §6.

---

M0 — Claude Code Implementation Checklist
0. M0 objective

Build M0 as a production-shaped foundation with one working vertical slice:

PDF
 ↓
Document registration
 ↓
Object storage
 ↓
PostgreSQL metadata
 ↓
PDF text extraction
 ↓
Document sections/chunks
 ↓
Pass-1 knowledge extraction
 ↓
Validation
 ↓
Neo4j knowledge graph
 ↓
Provenance query

M0 is successful when a developer can run:

make dev
make migrate
make test
make ingest SAMPLE=...

and inspect the resulting graph in Neo4j.

Do not implement in M0:

full PYQ discovery
web crawling
answer-key resolution
independent answer derivation
Hindi translation
question generation
explanations
difficulty grading
embeddings
human review UI
full M11 pipeline

Those remain later milestones.

1. Before writing code — inspect the repository
Claude Code tasks
 Inspect current repository.
 Read CLAUDE.md if present.
 Read docs/IMPLEMENTATION_PLAN.md.
 Identify existing backend/frontend structure.
 Identify existing Docker configuration.
 Identify existing PostgreSQL/Alembic setup.
 Identify whether pyproject.toml uses uv, Poetry, or another manager.
 Identify existing test conventions.
 Do not replace existing conventions unnecessarily.
 Produce a short implementation plan before modifying files.
Required output from Claude Code

Before coding, Claude should report:

Current architecture
Existing infrastructure
Files that will change
New files required
Dependencies to add
Potential conflicts
Implementation sequence

Do not let Claude Code start by rewriting the repository structure.

The existing implementation guide already defines the intended repository layout and explicitly separates API, domain logic, agents, rendering and integrations.

2. Establish repository structure

Target structure:

prashn-setu/
│
├── CLAUDE.md
├── README.md
├── Makefile
├── docker-compose.yml
├── .env.example
├── .gitignore
│
├── docs/
│   ├── IMPLEMENTATION_PLAN.md
│   └── adr/
│       ├── DEC-*.md
│       └── ...
│
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/
│   │   └── versions/
│   │
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   │
│   │   ├── api/
│   │   │   └── v1/
│   │   │
│   │   ├── core/
│   │   │
│   │   ├── db/
│   │   │
│   │   ├── models/
│   │   │
│   │   ├── schemas/
│   │   │
│   │   ├── repositories/
│   │   │
│   │   ├── services/
│   │   │
│   │   ├── ingestion/
│   │   │
│   │   ├── extraction/
│   │   │
│   │   ├── knowledge/
│   │   │   └── neo4j/
│   │   │
│   │   ├── agents/
│   │   │   └── question_bank/
│   │   │
│   │   └── integrations/
│   │
│   └── tests/
│       ├── unit/
│       ├── integration/
│       └── e2e/
│
└── frontend/
    └── ...
Important

Do not create:

agents/question_bank/full_pipeline.py

in M0.

The architecture needs independently testable pipeline steps. The implementation guide explicitly says the agents should be Celery-orchestrated pipelines, with every step individually resumable and testable.

3. Docker Compose foundation

Add:

PostgreSQL

Requirements:

PostgreSQL
pgvector
ltree
Neo4j

Use Neo4j Community Edition initially unless the existing deployment decision specifies otherwise.

Expose:

7474 → Neo4j Browser
7687 → Bolt
Object storage

Use an S3-compatible local service for development.

The implementation guide calls for S3-compatible object storage for source artifacts.

Services

M0 development stack:

postgres
neo4j
object-storage
backend
frontend

Do not add Kubernetes, Celery workers, vLLM, Redis clusters, monitoring stacks, etc. merely because they will exist later.

M0 should prove the architecture with minimum infrastructure.

4. Environment configuration

Create strongly typed settings.

Example categories:

APP_ENV

POSTGRES_HOST
POSTGRES_PORT
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD

NEO4J_URI
NEO4J_USERNAME
NEO4J_PASSWORD
NEO4J_DATABASE

S3_ENDPOINT
S3_REGION
S3_ACCESS_KEY
S3_SECRET_KEY
S3_BUCKET

LOG_LEVEL
Rules
 No credentials committed.
 .env ignored.
 .env.example committed.
 All configuration accessed through config.py.
 No os.getenv() scattered throughout application code.
 Tests must support isolated configuration.
5. FastAPI foundation

Implement:

GET /health
GET /ready
/health

Returns process health only.

/ready

Checks:

PostgreSQL
Neo4j
Object storage

Example:

{
  "status": "ready",
  "dependencies": {
    "postgres": "ok",
    "neo4j": "ok",
    "object_storage": "ok"
  }
}

If one dependency is unavailable:

HTTP 503
6. PostgreSQL foundation

Configure:

 SQLAlchemy
 Alembic
 async database access if consistent with current project architecture
 connection pooling
 migration command
 test database configuration
Initial M0 tables

Do not build the entire M5 question schema.

Create only the tables required for ingestion/extraction.

Suggested:

documents
document_sections
document_chunks
extraction_runs
extraction_results

Potential schema:

documents
id
checksum
filename
mime_type
storage_key
page_count
status
created_at
updated_at
document_sections
id
document_id
section_number
title
page_start
page_end
content
created_at
document_chunks
id
document_id
section_id
chunk_index
content
page_start
page_end
content_hash
created_at
extraction_runs
id
document_id
extractor_name
extractor_version
status
started_at
completed_at
metadata
extraction_results
id
extraction_run_id
chunk_id
result_json
status
validation_errors
created_at
7. Do not couple Neo4j to SQLAlchemy

Create a separate abstraction:

app/knowledge/neo4j/
    client.py
    repositories.py
    models.py
    schema.py

The application should never do this:

neo4j_session.run(...)

from random services.

Instead:

knowledge_graph_repository.create_entity(...)
knowledge_graph_repository.create_relationship(...)

This is important because Neo4j is the knowledge representation layer, not the transactional application database.

8. Neo4j initial graph model

Keep the M0 graph intentionally small.

Nodes
Document
DocumentSection
Chunk
Entity
Concept
Relationships
Document
  -[:HAS_SECTION]->
DocumentSection

DocumentSection
  -[:HAS_CHUNK]->
Chunk

Chunk
  -[:MENTIONS]->
Entity

Chunk
  -[:EXPRESSES]->
Concept

Entity
  -[:RELATED_TO]->
Entity

Do not prematurely create the entire final knowledge ontology.

9. Neo4j node identity

Every graph object needs a deterministic identity.

For example:

Document:
document:{document_id}

Section:
section:{section_id}

Chunk:
chunk:{chunk_id}

Entity:
entity:{canonical_entity_key}

Concept:
concept:{canonical_concept_key}
Critical rule

Never use Neo4j-generated internal IDs as business identifiers.

Use application-owned IDs.

10. Neo4j constraints

Create constraints/indexes for stable identities.

Conceptually:

CREATE CONSTRAINT document_id_unique
IF NOT EXISTS
FOR (d:Document)
REQUIRE d.id IS UNIQUE;

Equivalent constraints for:

DocumentSection
Chunk
Entity
Concept

Also add indexes for frequently queried provenance fields.

11. Neo4j provenance model

This is one of the most important M0 requirements.

Every knowledge object needs a trace back to source material.

For example:

(Entity)
    ↑
MENTIONS
    |
(Chunk)
    |
HAS_CHUNK
    |
(DocumentSection)
    |
HAS_SECTION
    |
(Document)

Every extracted entity should therefore be answerable with:

Where did this knowledge come from?

Add properties such as:

source_document_id
source_section_id
source_chunk_id
extraction_run_id
confidence

Do not rely exclusively on graph topology for provenance.

12. Object-storage service

Implement:

StorageService

Interface:

put_object(...)
get_object(...)
exists(...)
delete_object(...)

M0 needs:

put_object
get_object
exists
Storage path

Use deterministic keys such as:

documents/{document_id}/original.pdf

Never use the uploaded filename as the storage identity.

13. Document registration service

Implement:

DocumentService.register(...)

Input:

file
filename
mime_type

Process:

receive file
 ↓
calculate SHA-256
 ↓
check duplicate
 ↓
generate document_id
 ↓
store original
 ↓
create PostgreSQL record
Idempotency

If exactly the same document is uploaded twice:

same checksum
→ same document identity / duplicate detection

Do not silently create two independent copies.

14. PDF extraction interface

Create an abstraction:

class DocumentExtractor(Protocol):
    def extract(self, document: Document) -> ExtractedDocument:
        ...

Initial implementation:

PyMuPDFDocumentExtractor

The guide explicitly recommends native PDF extraction with pdfplumber / PyMuPDF where a text layer exists, with OCR only when necessary.

For M0:

Use PyMuPDF first.

Do not implement Sarvam OCR yet.

15. Extracted document representation

Create typed models.

Example:

ExtractedDocument
 ├── document_id
 ├── pages[]
 │    ├── page_number
 │    ├── text
 │    └── blocks[]
 └── metadata

A block should preserve:

block_id
page_number
text
bbox
block_type

Even if M0 only populates:

TEXT

the interface should permit later:

TEXT
IMAGE
TABLE
MATH
FIGURE
CAPTION

This matters because the implementation guide explicitly identifies layout-aware extraction, diagrams and maths as later extraction requirements.

16. Chunking

Implement:

DocumentChunker

Input:

ExtractedDocument

Output:

DocumentChunk[]

M0 chunking should be structure-aware, not simply:

text[:1000]

Preserve:

document
page
section
block
chunk

Each chunk gets:

chunk_id
document_id
section_id
page_start
page_end
content
content_hash
17. Pass-1 extraction

This is where I would deliberately keep M0 narrow.

Create:

app/extraction/pass1/
    extractor.py
    schemas.py
    prompts/
    validator.py
Pass 1 objective

Extract:

entities
concepts
relationships

from a chunk.

It is not the final Question Bank extraction pipeline.

18. Pass-1 schema

Use Pydantic.

Conceptually:

{
  "entities": [
    {
      "name": "...",
      "type": "...",
      "confidence": 0.94
    }
  ],
  "concepts": [
    {
      "name": "...",
      "confidence": 0.91
    }
  ],
  "relationships": [
    {
      "source": "...",
      "relationship": "...",
      "target": "...",
      "confidence": 0.87
    }
  ]
}

Every result must carry:

extraction_run_id
document_id
chunk_id
19. Extraction must NOT directly write Neo4j

This is a hard architectural rule.

Incorrect:

LLM
 ↓
Neo4j

Correct:

LLM
 ↓
ExtractionResult
 ↓
Schema validation
 ↓
Business validation
 ↓
Graph persistence

This separation lets us later compare:

Pass 1
Pass 2
Pass 3
Human correction

without destroying the original extraction.

20. Pass-1 validation

Implement deterministic validation before graph persistence.

Structural checks
 entities have names
 entity types are valid
 concepts have names
 relationship source exists
 relationship target exists
 relationship type is allowed
 confidence is [0,1]
 evidence/provenance exists
Invalid result

Do:

ExtractionResult
    status = INVALID

Do not write invalid graph objects.

21. Extraction confidence

Use confidence, but don't pretend that confidence itself means correctness.

Store:

confidence

but M0 should not auto-promote based solely on:

confidence > 0.8

The implementation guide's later verification model is much stricter: structural validation, source/key agreement, symbolic/model checks, mapping, duplicate checks, etc.

M0's confidence is therefore metadata, not a truth guarantee.

22. Graph persistence

Implement:

KnowledgeGraphWriter

with operations:

upsert_document
upsert_section
upsert_chunk
upsert_entity
upsert_concept
create_relationship

All operations must be idempotent.

Use:

MERGE

rather than blindly using:

CREATE
23. Graph write transaction

A single extraction result should preferably be persisted transactionally:

begin transaction

create/upsert entities
create/upsert concepts
create relationships
attach provenance

commit

If persistence fails:

rollback

No partially persisted extraction should be reported as successful.

24. Canonicalisation

Create:

EntityCanonicalizer
ConceptCanonicalizer

M0 can use simple deterministic normalization:

trim whitespace
case normalization
Unicode normalization
collapse repeated whitespace

But do not build sophisticated semantic entity resolution yet.

For example:

"Electromagnetic Induction"
"electromagnetic induction"

can normalize to the same canonical key.

But:

"EMI"
"Electromagnetic Induction"

should not automatically be merged unless the system has explicit evidence.

25. Graph query examples

Create integration tests for:

Document → chunks
MATCH (d:Document)-[:HAS_SECTION]->(:DocumentSection)
      -[:HAS_CHUNK]->(c:Chunk)
RETURN d, c
Chunk → entities
MATCH (c:Chunk)-[:MENTIONS]->(e:Entity)
RETURN c, e
Concept relationships
MATCH (e1:Entity)-[r:RELATED_TO]->(e2:Entity)
RETURN e1, r, e2
Provenance

Given an entity:

MATCH (e:Entity)<-[:MENTIONS]-(c:Chunk)
      <-[:HAS_CHUNK]-(s:DocumentSection)
      <-[:HAS_SECTION]-(d:Document)
RETURN e, c, s, d

This provenance path is a M0 acceptance test.

26. Extraction run lifecycle

Implement:

PENDING
RUNNING
SUCCEEDED
FAILED
INVALID

Flow:

create extraction_run
       ↓
RUNNING
       ↓
extract
       ↓
validate
       ↓
persist
       ↓
SUCCEEDED

Failure:

FAILED

Validation failure:

INVALID

Never mark a run SUCCEEDED if graph persistence failed.

27. Version extraction

Every extraction needs:

extractor_name
extractor_version
prompt_version
model_name

Example:

extractor_name = "pass1"
extractor_version = "0.1.0"
prompt_version = "pass1-v1"
model_name = "..."

This is essential for later reprocessing.

If the extraction logic changes:

pass1-v1
→
pass1-v2

we can compare results.

28. LLM abstraction

Do not couple Pass 1 directly to a particular model SDK.

Create:

LLMClient

with something like:

generate_structured(...)

M0 can have:

MockLLMClient

for deterministic tests.

Then later:

AIGatewayLLMClient

can be plugged in when M10 introduces the ai-gateway. The implementation plan intentionally puts the full AI gateway at M10, including routing, prompt registry, constrained decoding, token accounting and evaluation.

This is important: don't drag M10 into M0.

29. Prompt management

Create:

app/extraction/pass1/prompts/
    entity_relationship_extraction_v1.txt

and:

cases.yaml

The implementation guide already requires prompt regression discipline later: fixed cases with asserted properties and CI validation.

Implement the pattern now, even if the test set is tiny.

30. Deterministic mock extraction

Create a fixture:

sample_physics.pdf

or an equivalent small sample document.

For tests, mock the LLM:

Input chunk:
"Faraday's law describes electromagnetic induction..."

Expected:

Entity:
Faraday's Law

Entity:
Electromagnetic Induction

Relationship:
Faraday's Law
  RELATED_TO
Electromagnetic Induction

The test must not require an external LLM.

31. End-to-end ingestion command

Implement:

make ingest FILE=./samples/sample.pdf

Equivalent CLI:

python -m app.cli.ingest ./samples/sample.pdf

Output:

Document ID: ...
Checksum: ...
Pages: 4
Chunks: 12
Extraction Run: ...
Entities: 27
Concepts: 14
Relationships: 19
Graph persistence: SUCCESS
32. End-to-end test

The most important M0 test.

sample.pdf
 ↓
register
 ↓
store
 ↓
Postgres
 ↓
extract
 ↓
chunk
 ↓
Pass 1
 ↓
validate
 ↓
Neo4j
 ↓
query

Test assertions:

document exists
document stored
sections created
chunks created
extraction run succeeded
extraction result exists
entities exist in Neo4j
relationships exist
provenance exists
33. Idempotency test

Run ingestion twice.

Expected:

documents = 1
same checksum = detected

Run the same extraction twice.

Expected:

no duplicate Entity nodes
no duplicate relationships

This is a critical graph-quality test.

34. Failure tests

Test:

PostgreSQL unavailable
/ready → 503
Neo4j unavailable
/ready → 503
Object storage unavailable
document ingestion fails cleanly
Malformed PDF
extraction run → FAILED
Invalid LLM output
validation → INVALID
Neo4j → unchanged
Neo4j failure during persistence
transaction rollback
extraction run → FAILED
35. Logging

Use structured JSON.

Every extraction operation should contain:

request_id
document_id
chunk_id
extraction_run_id
operation
duration_ms
status

Example:

{
  "event": "extraction_completed",
  "document_id": "...",
  "extraction_run_id": "...",
  "chunks": 12,
  "entities": 27,
  "duration_ms": 1842,
  "status": "success"
}

The implementation guide explicitly calls for structured JSON logs and request IDs propagated into jobs and agent traces.

36. Metrics

M0 should establish metric names even if the full observability stack comes later.

At minimum:

documents_ingested_total
document_extraction_total
document_extraction_failures_total

extraction_duration_seconds
chunks_created_total

entities_extracted_total
concepts_extracted_total
relationships_extracted_total

neo4j_write_failures_total
37. CI pipeline

GitHub Actions should run:

lint
type-check
unit tests
integration tests
migration test
Docker Compose startup
E2E ingestion test

The existing plan explicitly requires a CI pipeline and an end-to-end hello test for M0.

Our revised M0 makes that final test much more valuable:

hello

becomes:

document → extraction → graph
38. Frontend

Keep the existing M0 requirement:

 Vite
 React
 TypeScript
 basic application shell
 API connectivity
 health status

Do not build the knowledge graph UI.

A minimal development page can show:

Prashn Setu

Backend      ✓
PostgreSQL   ✓
Neo4j        ✓
Storage      ✓

[ Upload sample document ]

Latest extraction:
Document
Chunks
Entities
Concepts
Relationships
Status

This is enough to make the M0 vertical slice demonstrable.

39. Makefile

Create:

make dev
make down
make logs

make migrate
make migration

make test
make test-unit
make test-integration
make test-e2e

make lint
make format
make typecheck

make ingest FILE=...
make seed
40. CLAUDE.md

Update CLAUDE.md with hard architectural rules.

Include:

# Architecture Rules

1. PostgreSQL is the transactional system of record.
2. Neo4j is the knowledge graph.
3. S3-compatible storage contains immutable source artifacts.
4. Extraction never writes directly to Neo4j.
5. Extraction produces a typed intermediate representation.
6. Graph writes happen only after validation.
7. Every graph fact must have provenance.
8. Graph writes must be idempotent.
9. Never use Neo4j internal IDs as domain IDs.
10. LLM calls must go through an abstraction.
11. M0 must not implement the complete M11 pipeline.
12. Every pipeline step must eventually be independently testable.
13. Never silently discard extraction failures.
14. Never overwrite an original source document.
41. ADRs

Create the following ADRs during M0.

DEC-M0-01

PostgreSQL + Neo4j dual persistence

Decision:

PostgreSQL = transactional system of record
Neo4j = knowledge graph
DEC-M0-02

Extraction intermediate representation

Decision:

LLM extraction
→ typed ExtractionResult
→ validation
→ graph
DEC-M0-03

Source provenance

Decision:

Every extracted graph fact must be traceable
to document + section + chunk + extraction run.
DEC-M0-04

Idempotent graph writes

Decision:

Application-owned deterministic IDs
+
MERGE
+
constraints
DEC-M0-05

Extraction versioning

Decision:

extractor version
+
prompt version
+
model version

are recorded for every extraction.

42. M0 acceptance test

Claude Code should not declare M0 complete until this exact scenario passes.

Input

One small real PDF.

Execute
make dev
make migrate
make test
make ingest FILE=samples/sample.pdf
Verify PostgreSQL
documents              → 1
document_sections      → N
document_chunks        → N
extraction_runs        → 1
extraction_results     → N
Verify Neo4j
Document               → 1
DocumentSection        → N
Chunk                  → N
Entity                 → N
Concept                → N
relationships           → N
Verify provenance

For every Entity:

Entity
 ↓
Chunk
 ↓
DocumentSection
 ↓
Document

must resolve.

Verify idempotency

Run:

make ingest FILE=samples/sample.pdf

again.

Expected:

no duplicate source document
no duplicate entities
no duplicate relationships
Verify failure isolation

Force invalid extraction output.

Expected:

ExtractionResult = INVALID

Neo4j:
unchanged
43. M0 completion report

Claude Code should finish by generating:

docs/milestones/M0_COMPLETION.md

containing:

## Implemented

## Architecture

## Files Added

## Files Modified

## Database Schema

## Neo4j Schema

## Extraction Contract

## Test Coverage

## E2E Result

## Known Limitations

## Deferred to M11

## ADRs

## How to Run
44. The M0 → M11 boundary

This is the most important thing I would put in the Claude Code instructions.

M0
SOURCE
 ↓
INGEST
 ↓
PARSE
 ↓
CHUNK
 ↓
PASS 1 EXTRACTION
 ↓
VALIDATE
 ↓
KNOWLEDGE GRAPH
M11

Eventually:

DISCOVER
 ↓
FETCH
 ↓
EXTRACT
 ↓
SEGMENT
 ↓
NORMALISE
 ↓
MAP
 ↓
RESOLVE
 ↓
VERIFY
 ↓
TRANSLATE
 ↓
EXPLAIN
 ↓
GRADE
 ↓
EMBED
 ↓
QUEUE

That separation follows the implementation guide rather than prematurely collapsing the whole agent into M0.