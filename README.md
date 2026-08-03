# Platform Django

A project template for building web applications with Django + Turborepo React.

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

## Tech Stack

- **Backend**: Django 5, Django REST Framework, Celery, PostgreSQL, Redis
- **Frontend**: React 19, Vite, Turborepo, Tailwind CSS, shadcn/ui
- **Tooling**: uv, pnpm, Lefthook, Ruff, ESLint, Prettier, mypy

## Making a Project From This Template

Nothing is renamed. A new project is a clone plus two values:

```bash
git clone https://github.com/mascah/platform-django.git acme-app
cd acme-app
bin/bootstrap
```

Then set the two in `.env`:

```bash
PROJECT_SLUG=acme_app            # names resources: databases, the deployed app
PROJECT_DISPLAY_NAME=Acme App    # what a user reads: titles, landing page, emails
```

`PROJECT_SLUG` defaults to the checkout's directory name, so two projects on one
machine already have separate databases, cache keys and task queues without
either being renamed. The internal Python package stays `platform_django` in
every project — that is the point, and it is invisible to users of the
application.

Adding domain modules and frontend applications is unaffected: those are
additions, named freely, and additions merge cleanly.

### Staying connected to the template

Because no file is renamed, an improvement is an ordinary merge in either
direction:

```bash
# Once, in the project
git remote add template https://github.com/mascah/platform-django.git

# Receive an improvement from the template
git fetch template
git merge template/main

# Contribute one back
git checkout -b improvement template/main
git cherry-pick <commit>
git push template improvement   # then open a pull request
```

The only files that routinely conflict are the append-mostly lists where a
project registers what it has added — `INSTALLED_APPS`, the root URL
configuration, `pnpm-workspace.yaml`, `.importlinter`. Keep them in template
order and conflicts stay cheap. See
[ADR-0006](docs/adr/0006-identity-as-data-no-rename.md).

### Ejecting

When a project has outgrown the template — its own infrastructure, its own
deployment story, nothing left it wants to receive — `bin/eject` ends the
arrangement:

```bash
bin/eject acme_app                      # display name derived: "Acme App"
bin/eject acme_app "ACME Rocket Sled"   # or given explicitly
```

It renames the package, the workspace application and every reference to them,
drops the `template` remote, regenerates the lockfiles, and deletes itself.
Links that point at the template's _own_ repository are left alone and listed,
because renaming a clone URL only produces one that resolves to nothing.

`PROJECT_SLUG` and `PROJECT_DISPLAY_NAME` stay — they are ordinary
configuration, not template scaffolding. Only their defaults move.

Ejecting is one way. It refuses to run against a dirty tree so that
`git reset --hard` is a real undo in the minute afterwards, but there is no
route back once you have built on it. Do it when you have decided you will never
merge with the template again; until then the rename buys nothing and costs you
the ability to. See [ADR-0007](docs/adr/0007-ejecting-from-the-template.md).

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
heroku create --manifest
git push heroku main
```

A prototype runs with no key-value store: the cache is in-process, background
tasks run inline, and mail goes to the dyno log. Graduating is a diff to
`app.json` plus a scale command — no code change.

## Architecture

See [CLAUDE.md](CLAUDE.md) for detailed architecture rules, module boundaries, and conventions.
