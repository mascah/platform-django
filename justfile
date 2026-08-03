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
serve:
    @uv run python manage.py runserver 0.0.0.0:${DJANGO_PORT}

# worker: Run a Celery worker against this worktree's Redis index.
worker:
    @uv run celery -A config.celery_app worker --loglevel=info

# beat: Run the Celery scheduler against this worktree's Redis index.
beat:
    @uv run celery -A config.celery_app beat --loglevel=info

# manage: Execute a Django management command.
manage +args:
    @uv run python manage.py {{args}}

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
