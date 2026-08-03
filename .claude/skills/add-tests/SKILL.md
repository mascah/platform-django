---
name: add-tests
description: Use proactively while implementing or modifying a feature anywhere in the repo. Classifies the change by layer, then writes the tests that accompany it — making tests part of the implementation rather than a follow-up.
---

# Add Tests

Read this skill **before** writing implementation code, not after. Classify the
change, then include the tests with it. The developer should have to remove a
test, not request one.

## Step 1 — Classify the change

A single change often spans several layers. Cover each one.

| Layer | Signals |
| --- | --- |
| **Django model** | New or changed field, constraint, validator, property, or migration under `platform_django/` |
| **Django service** | New or changed write path in `services.py` |
| **Django selector** | New or changed read path in `selectors.py` |
| **DRF endpoint** | New or changed viewset, action, serializer, route, or permission |
| **Celery task** | New or changed task, retry logic, or `on_commit` dispatch |
| **Django view or form** | New or changed server-rendered view, form, or template context |
| **React app** | New or changed component, hook, or route in `apps/platform_django/` |
| **Configuration or tooling** | New or changed settings, `bin/` script, or `justfile` recipe |

## Step 2 — Write the tests for each layer

### Django model — see the `django-model` skill

- Use `@pytest.mark.django_db`.
- Assert defaults, constraint violations (usually via `IntegrityError`), and any
  property output.
- Use the module's factory; `.build()` when no database write is needed.

### Django service — see the `django-service` skill

- Cover the success path: state persisted, outward effect triggered.
- Cover the primary failure path: missing record, precondition rejected.
- Use `django_capture_on_commit_callbacks(execute=True)` when the service
  schedules a post-commit effect.
- Assert observable state, not intermediate helper calls.

### Django selector — see the `django-selector` skill

- Assert the shape and filtering of what comes back.
- Assert the access scope: a row belonging to someone else is absent, not merely
  that the query returns.
- Cover the empty and not-found cases.

### DRF endpoint — see the `django-api` skill

- Drive DRF's `APIClient`. Do not construct the viewset.
- Cover: success status plus key response fields, `400` validation, `404` not
  found, `403` forbidden.
- Assert persisted state after a write, not just the response body.
- For any field that must not be writable, send it and assert it did not change.

### Celery task — see the `django-celery` skill

- Call the task function directly, not through `.delay()`.
- Assert the side effect and its exact arguments.
- Cover the retry path where retry logic exists.

### Django view or form

- Drive `django.test.Client` through the URL, as
  `platform_django/users/tests/test_views.py` does.
- Assert the redirect target and the persisted change, not the form instance.

### React app (`apps/platform_django/`)

The template wires no unit-test runner for this app: `pnpm test` runs a Turbo
task no package implements yet, and nothing depends on vitest. So:

- Cover user-visible behaviour with the Playwright suite in `e2e/`, which CI
  runs against Django plus the built frontend.
- If a component genuinely warrants unit tests, wire vitest into
  `apps/platform_django/` first and add its `test` script. The CI `vitest` job
  already runs `pnpm test`, so it will pick them up with no workflow change.
- Do not invent a runner in a single test file.

### Configuration or tooling

- `tests/` at the repository root holds the settings, environment and script
  tests. Add there, matching `tests/test_settings.py` and `tests/test_env.py`.

## Step 3 — Placement

| Layer | Location |
| --- | --- |
| Django, any | `platform_django/<module>/tests/test_<layer>.py`, API tests under `tests/api/` |
| Repo-level config and scripts | `tests/` |
| End-to-end | `e2e/tests/` |

Reuse existing factories, fixtures and conftest helpers. The global `user`
fixture is in `platform_django/conftest.py`. Add a new helper only when none
exists and at least two tests need it.

## Step 4 — Verify

Run the narrowest passing command before reporting done.

```bash
pytest platform_django/<module>/tests/test_services.py -k <name>   # focused
pytest platform_django/<module>/tests/                            # module
pnpm --filter e2e test                                            # end-to-end
```

`just coverage-check` enforces the 85% threshold.

## Default stance

If you are unsure whether a test adds value, write it and let the developer
decide. A rejected test costs one deletion; a missing one costs an incident.

Prefer the seam that survives refactoring. A test that drives the HTTP boundary
still passes when logic moves between a view and a service; a test that calls
`get_queryset()` on a view instance does not.

## References

- `docs/3-backend-guides/testing.rst`
- the `django-model`, `django-service`, `django-selector`, `django-api`,
  `django-celery` and `django-test` skills
- `platform_django/users/tests/` — the worked example for every Django shape
- `e2e/` — Playwright setup, fixtures and page objects
