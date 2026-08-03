---
name: new-python-lib
description: Use when creating a stateless Django-free Python package under libs/ — an API client, validator, transformation, or reusable integration — including uv workspace wiring and the isolation contract.
---

# New Python Lib

Reach for `libs/` only after checking the code really must stay stateless,
reusable and Django-free, and is not better as an addition to an existing lib or
as a module under `platform_django/`.

| Use `libs/` | Use `platform_django/<module>/` |
| --- | --- |
| Stateless code | Needs the Django ORM |
| No Django dependency | Needs Django settings, middleware or signals |
| Third-party API clients, validators, transforms | Needs the service/selector pattern |
| Returns Pydantic models or plain data | Owns persisted domain state |

`libs/` ships empty in the template. Yours will be the first, so there is no
neighbour to imitate — the shape below is the contract.

## Workflow

1. Scaffold: `uv init --package libs/<lib-name>`. Create the minimum files the
   behaviour needs. A JWT validator needs `jwt.py`, `schemas.py` and one test
   file; it does not need a generic `service.py`/`schemas.py`/factory scaffold.
2. Name the distribution with dashes and the import package with underscores,
   and keep the two corresponding.
3. Keep the lib pure Python. No `django`, no `platform_django`, no settings
   import. This is enforced, not merely advised — see the contract below.
4. Pass runtime inputs explicitly: base URLs, credentials, issuers, audiences,
   timeouts. Do not read global configuration. Configuration arrives through the
   constructor or the function signature.
5. Return typed results shaped to the integration — usually small Pydantic
   models, declared `frozen=True` when they are values rather than state.
6. Wire it up in the root `pyproject.toml`: add the distribution to
   `dependencies`, and add `<lib-name> = { workspace = true }` under
   `[tool.uv.sources]`. `[tool.uv.workspace]` already declares `members =
   ["libs/*"]`, so membership needs no edit.
7. Run `uv sync`.

## The Django wrapper

The lib never reads settings; the module that uses it injects them:

```python
# platform_django/<module>/clients.py
from django.conf import settings

from <lib_name> import Client


def client_get() -> Client:
    """Inject Django settings into the stateless lib."""
    return Client(api_url=settings.THING_API_URL, api_key=settings.THING_API_KEY)
```

That indirection is the whole point of the split: the lib is testable and
portable because it has never heard of Django, and the wrapper is the only place
that knows where configuration comes from.

## Import contract

Add the isolation contract to `.importlinter`. The template ships no
`libs-django-isolation` contract yet, because it ships no lib — create it with
the first one, and add each later lib to both lists:

```ini
[importlinter]
root_packages =
    platform_django
    <lib_name>

[importlinter:contract:libs-django-isolation]
name = Libs packages must not import Django or platform_django
type = forbidden
source_modules =
    <lib_name>
forbidden_modules =
    django
    platform_django
```

Without this the isolation is a convention, and the first agent that needs a
setting will import `django.conf` and nothing will stop it.

## Tests

Write focused tests against real validation or transformation behaviour. Patch
only the external boundary — the HTTP call, the clock — never the method under
test. Keep them Django-free: no `@pytest.mark.django_db`, no Django imports.

## Verification

From the repository root:

- `uv sync` when package metadata or workspace wiring changed
- `just libs-test-one <lib-name>`
- `uv run ruff check libs/<lib-name>` and `uv run ruff format --check libs/<lib-name>`
- `uv run mypy libs/<lib-name>`
- `uv run lint-imports`

## References

- `docs/2-architecture/module-structure.rst` — repo layout, Django-focused;
  secondary for libs
- `CONTEXT.md` — why a `libs/` package is not a Module
- `libs/README.md`
- `pyproject.toml` — `[tool.uv.workspace]` and `[tool.uv.sources]`
- `.importlinter`
