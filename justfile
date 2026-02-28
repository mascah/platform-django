# Docker compose command with worktree-specific env file (falls back if .env.local missing)
COMPOSE := if path_exists(".env.local") == "true" {
    "docker compose --env-file .env.local"
} else {
    "docker compose"
}

## Just does not yet manage signals for subprocesses reliably, which can lead to unexpected behavior.
## Exercise caution before expanding its usage in production environments.
## For more information, see https://github.com/casey/just/issues/2473 .


# Default command to list all available commands.
default:
    @just --list

# === Initial Setup ===

# setup: Run initial developer setup (installs tools, dependencies).
setup:
    @./bin/setup

# env-refresh: Refresh .env and .envrc from templates (preserves manual overrides).
env-refresh *args:
    @./bin/env-refresh {{args}}

# === Development ===

# ports: Show current worktree port configuration.
ports:
    @echo "Current port configuration:"
    @echo "  Django:              ${DOCKER_HOST_DJANGO_PORT:-8000}"
    @echo "  Vite:                ${VITE_PLATFORM_DJANGO_PORT:-5173}"
    @echo "  Postgres:            ${DOCKER_HOST_POSTGRES_PORT:-5432}"
    @echo "  Redis:               ${DOCKER_HOST_REDIS_PORT:-6379}"
    @echo "  Mailpit:             ${DOCKER_HOST_MAILPIT_PORT:-8025}"
    @echo "  Flower:              ${DOCKER_HOST_FLOWER_PORT:-5555}"

# up: Start all containers.
up:
    @echo "Building and starting containers..."
    @{{ COMPOSE }} up -d --remove-orphans

# down: Stop all containers.
down:
    @echo "Stopping containers..."
    @{{ COMPOSE }} down

# build: Build python image.
build:
    @echo "Building python image..."
    @{{ COMPOSE }} build django

# prune: Remove containers and their volumes.
prune *args:
    @echo "Killing containers and removing volumes..."
    @{{ COMPOSE }} down -v {{args}}

# rebuild: Stop, rebuild, and restart containers.
rebuild *args:
    @echo "Rebuilding containers..."
    @{{ COMPOSE }} down
    @{{ COMPOSE }} build {{args}}
    @{{ COMPOSE }} up -d --remove-orphans

# logs: View container logs.
logs *args:
    @{{ COMPOSE }} logs -f {{args}}

# shell: Open a shell in the Django container.
shell:
    @{{ COMPOSE }} exec django bash

# manage: Execute Django management command in container.
manage +args:
    @{{ COMPOSE }} exec django python manage.py {{args}}

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
