# .env is the one environment file, and it carries this worktree's database
# name, Redis index and application ports. Recipes below read it as ordinary
# environment variables; docker compose finds it by itself.
set dotenv-load := true

## Just does not yet manage signals for subprocesses reliably, which can lead to unexpected behavior.
## Exercise caution before expanding its usage in production environments.
## For more information, see https://github.com/casey/just/issues/2473 .


# Default command to list all available commands.
default:
    @just --list

# === Initial Setup ===

# bootstrap: Make this checkout runnable — toolchain, dependencies, .env.
bootstrap:
    @./bin/bootstrap

# setup: Developer conveniences on top of bootstrap (shell integration, git hooks).
setup:
    @./bin/setup

# env-refresh: Refresh .env from its template (preserves manual overrides).
env-refresh *args:
    @./bin/env-refresh {{args}}

# sync-agents: Regenerate the Codex and Cursor mirrors of .claude/skills and CLAUDE.md.
sync-agents:
    @./bin/sync-agents

# merge-template: Receive the template's improvements, settling what always
# settles the same way.
#
# Two kinds of file conflict on nearly every merge from the template, and they
# want opposite verbs.
#
# README.md and CONTEXT.md describe whichever repository they are in, so a
# project rewrites both and never wants the template's copy back. A rewritten
# file overlaps every hunk, so they conflict every time. They are kept.
#
# uv.lock and pnpm-lock.yaml are resolutions of the manifests rather than
# content, so neither side is the answer and a textual merge describes a
# resolution that never happened. They are regenerated. That can only be done
# once the manifests they resolve are settled, so a conflict in one of those
# stops the recipe instead.
#
# Anything else stops it too, because anything else is a real question.
#
# Deliberately not a merge=ours driver in .gitattributes: a driver is repo-wide
# and cannot tell this merge from an ordinary one, so it would also drop a
# branch's edits to those files during the project's own merges, with no
# conflict and no warning.
merge-template remote="template" branch="main":
    #!/usr/bin/env bash
    set -euo pipefail
    git fetch {{remote}}
    if git merge --no-edit {{remote}}/{{branch}}; then
        exit 0
    fi
    if ! git rev-parse -q --verify MERGE_HEAD >/dev/null; then
        echo "The merge did not start, so nothing was changed." >&2
        exit 1
    fi

    unmerged() { git ls-files --unmerged -- "$@" | grep -q .; }

    for file in README.md CONTEXT.md; do
        if unmerged "$file"; then
            git checkout --ours -- "$file"
            git add -- "$file"
            echo "Kept this project's $file"
        fi
    done

    # --theirs is the base to regenerate from, not the answer: it carries the
    # template's bumps in, and the locker then reconciles them against the
    # merged manifest, which is where this project's own dependencies are.
    if unmerged uv.lock; then
        if unmerged pyproject.toml; then
            echo "pyproject.toml conflicts. Resolve it, then: uv lock && git add uv.lock" >&2
        else
            git checkout --theirs -- uv.lock
            uv lock
            git add -- uv.lock
            echo "Regenerated uv.lock"
        fi
    fi
    if unmerged pnpm-lock.yaml; then
        if unmerged '*package.json' pnpm-workspace.yaml; then
            echo "A manifest conflicts. Resolve it, then: pnpm install --lockfile-only && git add pnpm-lock.yaml" >&2
        else
            git checkout --theirs -- pnpm-lock.yaml
            pnpm install --lockfile-only
            git add -- pnpm-lock.yaml
            echo "Regenerated pnpm-lock.yaml"
        fi
    fi

    if git ls-files --unmerged | grep -q .; then
        echo ""
        echo "Conflicts remain. Resolve them, then run: git commit" >&2
        exit 1
    fi
    git commit --no-edit

# === Backing Services ===
#
# One Postgres and one Redis serve every worktree on this machine, so these
# recipes act on containers shared with any other session — `just down` stops
# them for everyone. Worktrees isolate by database and Redis index instead.

# up: Start the shared backing services and ensure this worktree's database exists.
up:
    #!/usr/bin/env bash
    set -euo pipefail
    docker compose up -d --wait
    if [[ -z "$(docker compose exec -T postgres psql -U "$POSTGRES_USER" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname = '$POSTGRES_DB'")" ]]; then
        docker compose exec -T postgres createdb -U "$POSTGRES_USER" "$POSTGRES_DB"
        echo "Created database $POSTGRES_DB"
    fi

# down: Stop the shared backing services (affects every worktree).
down:
    @docker compose down

# prune: Remove the shared backing services and their data (affects every worktree).
prune *args:
    @docker compose down -v {{args}}

# logs: View backing service logs.
logs *args:
    @docker compose logs -f {{args}}

# psql: Open a psql shell on this worktree's database.
psql:
    @docker compose exec postgres psql -U "$POSTGRES_USER" "$POSTGRES_DB"

# === Development ===
#
# Django, Vite and Celery are application processes and run on the host.

# ports: Show this worktree's configuration.
ports:
    @echo "Worktree configuration (from .env):"
    @echo "  Django:    http://localhost:${DJANGO_PORT}"
    @echo "  Vite:      http://localhost:${VITE_PORT}"
    @echo "  Database:  ${POSTGRES_DB} on ${POSTGRES_HOST}:${POSTGRES_PORT}"
    @echo "  Redis:     index ${REDIS_DB} on ${REDIS_HOST}:${REDIS_PORT}"
    @echo "  Mailpit:   http://localhost:8025"

# serve: Run the Django development server on this worktree's port.
#
# Loopback rather than 0.0.0.0, because runserver prints the address it bound
# and that line is the one a developer clicks. http://0.0.0.0:8000/ is not a
# potentially trustworthy origin, so the browser drops the COOP header, and
# Vite's dev server refuses it as a cross-origin request, which reads as an
# app that will not load. To reach this server from another machine, forward
# the port over SSH rather than widening the bind — the origin stays localhost
# and nothing here has to change.
serve:
    @uv run python manage.py runserver 127.0.0.1:${DJANGO_PORT}

# worker: Run a Celery worker against this worktree's Redis index.
worker:
    @uv run celery -A config.celery_app worker --loglevel=info

# beat: Run the Celery scheduler against this worktree's Redis index.
beat:
    @uv run celery -A config.celery_app beat --loglevel=info

# manage: Execute a Django management command.
manage +args:
    @uv run python manage.py {{args}}

# openapi: Regenerate the TypeScript API client from the current Django schema.
#
# Dumps the schema rather than fetching it from a running server, so this needs
# neither `just serve` nor knowledge of this worktree's port. CI runs the same
# two commands and fails if the result differs from what is committed.
openapi:
    #!/usr/bin/env bash
    set -euo pipefail
    schema="$(mktemp -t openapi-schema.XXXXXX)"
    trap 'rm -f "$schema"' EXIT
    uv run python manage.py spectacular --file "$schema"
    cd apps/platform_django && pnpm openapi-ts -i "$schema"

# lintmigrations: Flag migrations on this branch that break a rolling deploy.
#
# Always scoped to what the branch added. Run bare, the linter walks every
# migration in the project, including third-party ones it cannot `sqlmigrate` --
# allauth's mfa migration raises rather than reporting. CI runs this same
# command.
lintmigrations base="origin/main":
    @uv run python manage.py lintmigrations --git-commit-id {{base}} --project-root-path .

# === Deployment ===

# provision: Create and deploy a Heroku app from app.json. Pass --dry-run first.
provision *args:
    @./bin/provision {{args}}

# === Documentation ===

# docs: Build documentation.
docs:
    @echo "Building documentation..."
    @uv run sphinx-build -M html docs docs/_build

# docs-serve: Serve documentation with live reload.
docs-serve:
    @echo "Starting documentation server at http://localhost:9000..."
    @uv run sphinx-autobuild -b html --port 9000 --watch platform_django docs docs/_build/html

# docs-clean: Clean documentation build artifacts.
docs-clean:
    @echo "Cleaning documentation build..."
    @rm -rf docs/_build

# graph: Generate Django model dependency graph.
graph:
    @echo "Generating model dependency graph..."
    @uv run python manage.py graph_models -a -g -o docs/models.svg

# === Libs (Isolated Python Packages) ===

# libs-test: Run tests for all isolated Python packages (no Django required).
libs-test:
    #!/usr/bin/env bash
    echo "Running libs tests..."
    for lib in libs/*/; do
        lib_name=$(basename "$lib")
        echo "Testing $lib_name..."
        uv run pytest "$lib/tests/" -v --override-ini="addopts="
    done

# libs-test-one: Run tests for a specific lib.
libs-test-one lib:
    uv run pytest libs/{{lib}}/tests/ -v --override-ini="addopts="

# === Coverage ===

# coverage: Run tests with coverage report
coverage:
    @echo "Running tests with coverage..."
    @uv run pytest --cov --cov-report=html --cov-report=term-missing

# coverage-report: Open coverage HTML report in browser
coverage-report:
    @uv run pytest --cov --cov-report=html -q
    @open htmlcov/index.html || xdg-open htmlcov/index.html

# coverage-check: Verify coverage meets minimum threshold
coverage-check:
    @echo "Checking coverage threshold..."
    @uv run pytest --cov --cov-fail-under=85 -q

coverage-clean:
    @echo "Cleaning coverage artifacts..."
    @rm -f .coverage
    @rm -rf htmlcov

py-clean: coverage-clean
    @echo "Cleaning Python artifacts..."
    @find . -type d -name "__pycache__" -prune -exec rm -rf {} \; || true
    @rm -rf .pytest_cache .mypy_cache .ruff_cache .import_linter_cache .grimp_cache staticfiles

js-clean:
    @echo "Cleaning JavaScript artifacts..."
    @find . -type d -name "node_modules" -prune -exec rm -rf {} \; || true
    @find . -type d -name "dist" -prune -exec rm -rf {} \; || true
    @find . -type d -name ".turbo" -prune -exec rm -rf {} \; || true

[parallel]
clean-all: docs-clean coverage-clean py-clean js-clean
    @echo "All clean!"
