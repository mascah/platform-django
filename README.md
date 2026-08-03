# Platform Django

A project template for building web applications with Django + Turborepo React.

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

## Tech Stack

- **Backend**: Django 5, Django REST Framework, Celery, PostgreSQL, Redis
- **Frontend**: React 19, Vite, Turborepo, Tailwind CSS, shadcn/ui
- **Tooling**: uv, pnpm, Lefthook, Ruff, ESLint, Prettier, mypy

## Quick Start

```bash
# 1. Run the setup script (installs tools, dependencies, generates .env)
just setup

# 2. Start the Docker stack (Django, Postgres, Redis, Celery, Mailpit)
just up

# 3. Run database migrations
just manage migrate

# 4. Start the Vite dev server (runs on host)
pnpm dev
```

## Development

```bash
just up              # Start Docker stack
just down            # Stop Docker stack
just logs            # View container logs
just manage <cmd>    # Run manage.py in container
just serve           # Run Django on this worktree's port
pnpm dev             # Run Vite dev servers
```

## Testing

```bash
pytest                  # Run Django tests
pnpm test               # Run frontend tests
pnpm test:e2e           # Run Playwright E2E tests
just coverage           # Run tests with coverage report
just libs-test          # Run tests for libs/ packages
```

## Deploying

`app.json` is the manifest: buildpack order (frontend, then Python), the minimum
add-ons, the configuration variables, and a formation with only the web process
scaled. Provisioning a prototype is one command against it:

```bash
heroku create --manifest
git push heroku main
```

A prototype runs with no key-value store: the cache is in-process, background
tasks run inline, and mail goes to the dyno log. Graduating is a diff to
`app.json` plus a scale command — no code change.

## Architecture

See [CLAUDE.md](CLAUDE.md) for detailed architecture rules, module boundaries, and conventions.
