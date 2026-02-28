# CLAUDE.md

## Project Overview

Modular monolith Django + Turborepo React for building web applications.

## Commands

### Development

- `just setup` — Run initial developer setup (installs tools, dependencies)
- `just env-refresh` — Refresh .env/.envrc from templates (preserves manual overrides)
- `just up` — Start Docker stack (Django, Postgres, Redis, Celery, etc.)
- `just down` — Stop Docker stack
- `just rebuild` — Stop, rebuild, and restart containers
- `just prune` — Remove containers and their volumes
- `just logs` — View container logs
- `just manage <cmd>` — Run manage.py in container
- `just shell` — Open bash shell in Django container
- `just ports` — Show current worktree port configuration
- `pnpm dev` — Run Vite dev server (runs on host)

### Testing & Quality

- `pytest` — Run tests
- `just libs-test` — Run tests for all isolated Python packages (no Django)
- `just libs-test-one <name>` — Run tests for a specific lib
- `just coverage` — Run tests with coverage (HTML + terminal)
- `just coverage-report` — Open coverage HTML in browser
- `just coverage-check` — Check minimum 85% threshold
- `mypy platform_django` — Type check
- `ruff check . && ruff format .` — Lint/format

### Frontend

- `pnpm install && pnpm dev` — Install and run Vite dev servers
- `pnpm build` — Build all apps
- `pnpm lint` — Lint all apps
- `pnpm typecheck` — Type check all apps
- `pnpm format` — Format with Prettier
- `cd apps/platform_django && pnpm openapi-ts` — Regenerate API client (after API changes)

### Documentation

- `just docs` — Build Sphinx documentation
- `just docs-serve` — Serve docs with live reload (<http://localhost:9000>)
- `just clean-all` — Clean all build artifacts (Python, JS, docs)

## Worktree Development

This project supports parallel development using git worktrees. Each worktree runs Docker services on isolated ports managed by a central registry.

### Port Registry System

Ports are allocated from a pool (Django 8001-8011, main uses 8000) and stored in `~/.platform-django-worktree-ports.json`. All service ports are calculated from the same offset to avoid conflicts.

```bash
# View all port allocations
bin/worktree-ports list

# Check registry status
bin/worktree-ports status

# Clean up stale entries (deleted worktrees)
bin/worktree-ports cleanup
```

### Port Discovery

```bash
just ports
# Output: Django: 8000, Vite: 5173 (or worktree-specific ports)
```

### Creating a New Worktree

```bash
# From any worktree
. bin/worktree-new feature-branch
```

This allocates the next available port from the registry and generates `.env.local` with all service ports:

- `DOCKER_HOST_DJANGO_PORT`, `DOCKER_HOST_POSTGRES_PORT`, `DOCKER_HOST_REDIS_PORT`, etc. — Docker host port mappings
- `VITE_PLATFORM_DJANGO_PORT` — Vite dev server port (runs on host)
- `WORKTREE_ID` — Used for Docker container naming

### Removing a Worktree

```bash
# From within the worktree to remove
. bin/worktree-remove
```

This releases the port allocation back to the pool.

### Starting Development

```bash
# 1. Start Docker stack
just up

# 2. Start Vite dev server (runs on host, uses VITE_PLATFORM_DJANGO_PORT)
pnpm dev
```

### OpenAPI Client Generation

Django must be running first:

```bash
cd apps/platform_django && pnpm openapi-ts
```

### Database Considerations

Each worktree can have its own isolated PostgreSQL database via docker-compose:

- **Migrations**: Run `just manage migrate` in each worktree
- **Testing**: pytest uses a separate test database (safe to run in parallel)

### Dependencies

- `jq` required for port registry management: `brew install jq`

## Architecture Rules (CRITICAL)

### Isolated Python Packages (`libs/`)

Stateless Python packages that don't depend on Django live in `libs/`. These are managed as uv workspace members with their own `pyproject.toml` and tests.

**When to use `libs/` vs `platform_django/`:**

- `libs/` — Stateless code, no Django dependency, returns Pydantic models (e.g., third-party API clients, data transformations)
- `platform_django/<module>/` — Code that needs Django ORM, settings, middleware, or the service/selector pattern

**Creating a new lib:**

```bash
uv init --package libs/<lib-name>
# Then add to root pyproject.toml: dependencies and [tool.uv.sources]
# Then add to .importlinter: source_modules in libs-django-isolation contract
```

**Rules:**

- Libs must **never** import from `django` or `platform_django` (enforced by import-linter)
- Use dependency injection for configuration (accept parameters, not `django.conf.settings`)
- Django modules create thin wrappers that inject settings into lib classes

### Module Boundaries

- Modules live in `platform_django/<module>/`
- **No foreign keys between modules** — use integer IDs
- Cross-module communication via domain events only
- Return dataclasses (DTOs) for cross-module calls

### Service/Selector Pattern

- `services.py` — Write operations (business logic)
- `selectors.py` — Read operations (queries)
- Views are thin — orchestrate services/selectors only
- Never put logic in models, views, or signals

### Module Structure

```bash
platform_django/<module>/
├── models.py       # Domain models
├── services.py     # Write operations
├── selectors.py    # Read operations
├── api/            # Views, serializers, urls
└── tests/
```

### Event-Driven Communication

- Publish events with `transaction.on_commit()` — never before commit
- Events are past-tense dataclasses (e.g., `OrderPlacedEvent`)
- Event bus: `platform_django/domain_events/bus.py`
- Register handlers in `AppConfig.ready()` with lazy imports

## Frontend Integration

- Django serves React SPAs via `django-vite`
- API client generated from OpenAPI schema (`drf-spectacular`)
- Auth: `django-allauth` headless at `/_allauth/`
- UI components: `@workspace/ui` (shadcn/ui with Tailwind CSS)

## Code Quality

- Pre-commit hooks run automatically (Lefthook)
- **NEVER use `--no-verify`** — blocked in settings
- Python: ruff, mypy, import-linter
- Frontend: ESLint, Prettier, tsc

## Testing

- `pytest` with `@pytest.mark.django_db`
- `FakeEventBus` for testing event handlers
- `django_capture_on_commit_callbacks` for transaction tests
- No secrets in code — use environment variables
