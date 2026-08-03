---
name: new-django-module
description: Use when creating or reviewing a new Django module (bounded context) under platform_django/, including app registration, API routing, tests, and import-linter placement.
---

# New Django Module

Start by proving a new module is warranted. Read
`docs/2-architecture/module-structure.rst` and `.importlinter`, then inspect
`platform_django/users/`, `LOCAL_APPS` in `config/settings/base.py`, and route
registration in `config/api_router.py`.

A module is a Django bounded context under `platform_django/`. It owns its
models, its writes, its reads and its migrations, and it is the unit the
dependency rules and import contracts apply to. A `libs/` package, a frontend
application and a shared frontend package are none of them modules.

## Decide first

- **Extend an existing module** if the behaviour mostly shares models,
  lifecycle, and rules with it. This is usually the right answer.
- **Create a new module** only when ownership and boundary rules are distinct
  enough to justify another app. A prototype is expected to run on `core`,
  `users` and one module of its own.
- Place it at the feature level: it may depend on `users` and `core`, and a
  dependency on another feature module must be declared explicitly.

## Build only what the behaviour needs

Do not scaffold `startapp` output or placeholder files. Typical files:

- always: `platform_django/<module>/__init__.py`, `apps.py`
- `models.py` and `migrations/` only if new models are required
- `services.py` for writes and `selectors.py` for reads, when that behaviour
  exists
- `api/` only if the module exposes endpoints
- `tests/` only for the behaviour you added

While implementing:

- Keep writes in services and reads in selectors. Prefer `entity_action` names,
  and keyword-only parameters when an operation takes two or more inputs.
- Keep Celery tasks thin, and dispatch after commit with stable primitives.
- Direct downward service calls are valid; domain events are not the default.
- Decide cross-module foreign keys case by case, with a stated justification.
- Match the shape of `users/` rather than forcing a layout of your own.

## Registration

- Add the app to `LOCAL_APPS` in `config/settings/base.py`.
- Register routes in `config/api_router.py`, or include a module-level
  `api/urls.py` from `config/urls.py`, only if the module exposes endpoints. A
  viewset that builds its queryset from a selector needs an explicit
  `basename`.
- `just manage makemigrations <module>` if the module has models.

## Import contracts

Update `.importlinter` in the same change. Inspect the current file rather than
trusting a remembered list; the template ships three contracts today:

- `infrastructure-isolation` — add `platform_django.<module>` to
  `forbidden_modules`, so `core` still cannot import a business module.
- `<module>-internal-layers` — add a layers contract mirroring
  `users-internal-layers`, listing **only layers that actually exist**.
  Parenthesise a layer you are declaring for later, as `(tasks)` is there.
  A contract naming layers that do not exist passes vacuously and proves
  nothing — that defect is what #91 was written about.
- Consider a `forbidden` contract keeping your API views off the ORM, as
  `api-views-do-not-query` does for `users`. A layers contract cannot catch a
  write reimplemented inside a view.

Add a feature-to-feature isolation contract when your project gains a second
feature module and the direction between them matters.

## Tests

Add only tests the new behaviour requires, covering its public write, read, API
and boundary behaviour. Prefer the HTTP seam. Follow the organization in
`platform_django/users/tests/`; filenames and class names are not gates.

## Verification

- `pytest platform_django/<module>/tests`
- `uv run lint-imports`
- `uv run ruff check platform_django/<module> config/settings/base.py config/api_router.py`
- `uv run mypy platform_django/<module>`
- if models were added: `just manage makemigrations <module> --check --dry-run`

## References

- `docs/2-architecture/module-structure.rst` — layout and naming
- `docs/2-architecture/module-boundaries.rst` — what each contract asserts
- `docs/2-architecture/module-dependencies.rst` — module levels
- `CONTEXT.md` — the definitions of Module, Service and Selector
- `platform_django/users/` — the module to imitate
- `.importlinter`, `config/settings/base.py`, `config/api_router.py`
