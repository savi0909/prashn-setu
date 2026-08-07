# Target names are fixed by Appendix E. Every target listed there must exist —
# "a target that only lives in someone's shell history is not a target". Targets
# for milestones not yet reached fail loudly with the milestone that adds them,
# rather than being absent or silently passing.

.DEFAULT_GOAL := help
BACKEND := backend
# The uv cache and this repo are often on different drives; copy avoids a
# hardlink warning on every invocation.
export UV_LINK_MODE := copy
UV := uv --directory $(BACKEND)
# Same venv, but cwd stays at the repo root — pre-commit resolves
# .pre-commit-config.yaml and .git/hooks relative to the working directory.
UV_ROOT := uv run --project $(BACKEND)

define todo
	@echo "make $@ — not implemented until $(1)." && exit 1
endef

.PHONY: help
help: ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

.PHONY: install
install: ## Install backend dependencies and git hooks (provisions CPython 3.12 via uv)
	$(UV) sync --all-groups
	# Not `pre-commit install`: that refuses to run when core.hooksPath is set,
	# and overwriting a developer's global hooks would be the wrong fix. The
	# dispatchers in .githooks/ chain to the global hooks instead.
	git config core.hooksPath .githooks

.PHONY: hooks
hooks: ## Run every pre-commit hook against all files
	$(UV_ROOT) pre-commit run --all-files

# ---------------------------------------------------------------- compose

.PHONY: up
up: ## Start the local stack (postgres + redis + minio; api/worker/web from M0 full)
	docker compose up -d --wait

.PHONY: down
down: ## Stop containers, keep volumes
	docker compose down

.PHONY: logs
logs: ## Tail container logs
	docker compose logs -f

.PHONY: nuke
nuke: ## Stop containers AND delete volumes (destroys local data)
	docker compose down -v

.PHONY: dev
dev: ## Run the API with reload
	$(UV) run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# ---------------------------------------------------------------- database

.PHONY: migrate
migrate: ## Apply migrations to head
	$(UV) run alembic upgrade head

.PHONY: migrate-down
migrate-down: ## Roll back one revision
	$(UV) run alembic downgrade -1

.PHONY: migration
migration: ## Autogenerate a revision: make migration name="add examinations"
	@test -n "$(name)" || (echo 'usage: make migration name="add examinations"' && exit 1)
	$(UV) run alembic revision --autogenerate -m "$(name)"

.PHONY: migrate-check
migrate-check: ## Prove migrations round-trip: head -> base -> head
	$(UV) run alembic upgrade head
	$(UV) run alembic downgrade base
	$(UV) run alembic upgrade head

.PHONY: seed
seed: ## Reference data: boards, subjects, class levels, P0 examinations, demo org
	$(call todo,M4)

.PHONY: seed-questions
seed-questions: ## 200 demo questions across three examinations
	$(call todo,M5)

# ---------------------------------------------------------------- quality

.PHONY: lint
lint: ## ruff check + format check
	$(UV) run ruff check .
	$(UV) run ruff format --check .

.PHONY: format
format: ## Apply ruff formatting and autofixes
	$(UV) run ruff check --fix .
	$(UV) run ruff format .

.PHONY: typecheck
typecheck: ## mypy
	$(UV) run mypy app

# ---------------------------------------------------------------- tests

.PHONY: test
test: test-backend ## Full test suite (frontend joins at M0 full)

.PHONY: test-backend
test-backend: ## Backend unit + integration
	$(UV) run pytest

.PHONY: test-domain
test-domain: ## Pure logic only, no I/O — must stay under 5 seconds (§13.1)
	$(UV) run pytest tests/unit

.PHONY: test-frontend
test-frontend: ## Vitest
	$(call todo,M0 full — frontend skeleton)

.PHONY: e2e
e2e: ## Playwright against the running stack
	$(call todo,M8)

# ---------------------------------------------------------------- contracts

.PHONY: openapi
openapi: ## Regenerate openapi.json; CI fails if the diff is non-empty
	$(UV) run python -m app.scripts.dump_openapi

# ---------------------------------------------------------------- ai

.PHONY: eval
eval: ## Golden-set evaluation against cassettes
	$(call todo,M10)

.PHONY: eval-live
eval-live: ## Golden-set evaluation against real models
	$(call todo,M10)

.PHONY: check
check: lint typecheck test ## Everything CI runs
