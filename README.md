# Platform Django

A project template for building web applications with Django + Turborepo React.

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

## Tech Stack

- **Backend**: Django 5, Django REST Framework, Celery, PostgreSQL, Redis
- **Frontend**: React 19, Vite, Turborepo, Tailwind CSS, shadcn/ui
- **Tooling**: uv, pnpm, Lefthook, Ruff, ESLint, Prettier, mypy

## Making a Project From This Template

Nothing is renamed. A new project is a clone plus two values in `.env`:

```bash
git clone https://github.com/mascah/platform-django.git acme-app
cd acme-app
bin/bootstrap
```

`PROJECT_SLUG` defaults to the checkout's directory name; set
`PROJECT_DISPLAY_NAME` beside it. The internal Python package stays
`platform_django` in every project — that is the point, and it is invisible to
users of the application.

What to change afterwards, what a merge from the template costs, and how to
eject are in
[Working With the Template](docs/1-getting-started/staying-connected.rst).
See also [ADR-0006](docs/adr/0006-identity-as-data-no-rename.md).

> **Made a project from this?** Everything below is true of it as written. This
> section is the only one to delete, along with the title and tagline above.

## Quick Start

```bash
# 1. Make the checkout runnable (toolchain, dependencies, .env)
bin/bootstrap

# 2. Start the shared backing services (Postgres, Redis, Mailpit)
just up

# 3. Run database migrations
just manage migrate

# 4. Start Django and the Vite dev server (both host processes)
just serve
pnpm dev
```

## Development

```bash
just up              # Start the shared backing services
just down            # Stop them (affects every worktree)
just logs            # View backing service logs
just manage <cmd>    # Run manage.py
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
just provision --dry-run   # print what it would do; everything after create bills
just provision
```

No Heroku CLI command reads `app.json` — `heroku create --manifest` reads
`heroku.yml`, a different format whose setup section is only honoured on the
container stack. So `bin/provision` applies the manifest itself, in the order
Heroku constrains: create, buildpacks, add-ons, config, push, scale.

Merging a pull request does not deploy this app. Review apps deploy branches and
are destroyed on merge; a production app deploys when its pipeline has
**Automatic deploys** enabled for it, or when `just provision` is run again.

A prototype runs with no key-value store: the cache is in-process, background
tasks run inline, and mail goes to the dyno log. Graduating is a diff to
`app.json` plus a scale command — no code change.

## Architecture

See [CLAUDE.md](CLAUDE.md) for detailed architecture rules, module boundaries, and conventions.
