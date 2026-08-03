# CLAUDE.md

## Project Overview

Modular monolith Django + Turborepo React for building web applications.

## Commands

### Development

- `bin/bootstrap` — Make a fresh checkout runnable (toolchain, dependencies, .env). Assumes no package manager
- `just setup` — Developer conveniences on top of bootstrap (shell integration, git hooks)
- `just env-refresh` — Refresh .env from its template (preserves manual overrides)
- `just up` — Start the shared backing services (Postgres, Redis, Mailpit) and create this worktree's database
- `just down` — Stop the shared backing services (affects every worktree)
- `just prune` — Remove the shared backing services and their data (affects every worktree)
- `just logs` — View backing service logs
- `just psql` — Open a psql shell on this worktree's database
- `just serve` — Run Django on this worktree's port (host process)
- `just worker` / `just beat` — Run Celery against this worktree's Redis index
- `just manage <cmd>` — Run manage.py
- `just ports` — Show this worktree's ports, database and Redis index
- `pnpm dev` — Run Vite dev server

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

This project supports parallel development using Claude Code's `--worktree` flag. Worktrees share the machine's backing services and isolate by database name and Redis index.

### Creating a Worktree

```bash
# Start Claude Code in an isolated worktree
claude --worktree feature-name

# Auto-generated name
claude --worktree
```

This automatically:

1. Creates a git worktree at `.claude/worktrees/{name}`
2. Generates `.env` with its own database name, Redis index and application ports
3. Installs Python and Node dependencies

When you exit the session, Claude prompts to keep or remove the worktree.

### Isolation

One Postgres and one Redis serve every worktree on the machine, so a worktree does not run a stack of its own. It isolates by:

- **Database** — `{PROJECT_SLUG}_{worktree}`, alongside the main checkout's `{PROJECT_SLUG}`
- **Redis logical index** — `REDIS_DB`, one per worktree (Redis serves 16)
- **Application ports** — `DJANGO_PORT` and `VITE_PORT`, the only ports that need allocating, since Django and Vite run on the host

`bin/env-refresh` works those out on first write and puts them in `.env`, which is the record of what the worktree took — sibling worktrees are read out of their own `.env` files, so there is no registry to go stale and nothing to clean up.

```bash
# Show this worktree's ports, database and Redis index
just ports
```

### Working in a Worktree

```bash
# 1. Start the shared backing services and create this worktree's database
just up

# 2. Start Django (host process, on this worktree's port)
just serve

# 3. Start the Vite dev server
pnpm dev
```

`just down` and `just prune` act on the shared containers, so they affect every worktree.

### OpenAPI Client Generation

Django must be running first:

```bash
cd apps/platform_django && pnpm openapi-ts
```

### Database Considerations

Each worktree gets its own database on the shared Postgres, created by `just up`:

- **Migrations**: Run `just manage migrate` in each worktree
- **Testing**: pytest uses a separate test database (safe to run in parallel)

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

## Agent skills

### Issue tracker

Issues live as GitHub issues in `mascah/platform-django`, managed with the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

The five canonical triage roles, each label string equal to its name (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context — one `CONTEXT.md` plus `docs/adr/` at the repo root, created lazily as terms and decisions get resolved. See `docs/agents/domain.md`.
