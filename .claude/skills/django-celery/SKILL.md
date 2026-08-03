---
name: django-celery
description: Use when adding, changing, or reviewing Celery tasks, retries, acknowledgements, scheduling, queues, or transaction-safe task dispatch under platform_django/.
---

# Django Celery

Read the target task, its service caller, and the nearest task and service tests
before editing. Match current module code before older prose.

The template ships no Celery task. The first one you add makes the `(tasks)`
layer in `.importlinter` real — it is parenthesised precisely so its position in
the hierarchy is already declared: `api` and `views` above it, `services` and
`selectors` below.

## Decide

- Keep tasks thin. A task may own retry, acknowledgement, queue and countdown
  scheduling, and operational logging. Reads belong in selectors and writes or
  workflow mutations belong in services.
- Dispatch from services after commit, with stable primitives or DTO fields. Do
  not close over ORM instances in `transaction.on_commit()` callbacks.

  ```python
  order_id = order.pk
  transaction.on_commit(lambda: order_confirm_task.delay(order_id))
  ```

- Use retry and acknowledgement behavior only where the task itself needs it.
- Treat pre-commit dispatch as a protocol exception, taken only when the path
  documents and tests why broker acknowledgement must precede commit.
- Design tasks to be idempotent. A retried task runs again against state its
  first attempt may already have changed.

## Dispatch runs inline without Redis

`CELERY_TASK_ALWAYS_EAGER` is on whenever no Redis URL is configured, so
`.delay()` executes the task synchronously in the calling process rather than
hanging on a broker that is not there. That is what lets a Tier 0 prototype
deploy without a worker.

The consequence is a task's cost lands in the request that dispatched it, and
its exceptions surface there. A task whose work is only tolerable in the
background is a reason to provision Redis and run `just worker` — not a reason
to work around eager mode.

The default queue is named after `PROJECT_SLUG`, because one Redis serves every
project on a development machine and two projects on Celery's shared `celery`
queue would each run the other's tasks. Workers consume it by default; nothing
has to name it.

## Tests

- Add targeted tests near the task or the service you changed.
- For ordinary service dispatch, capture `on_commit` callbacks with
  `django_capture_on_commit_callbacks(execute=True)` and assert the exact stable
  task arguments at the use site. Patch the callback target where it is used,
  not where it was defined.
- For task wrappers, test retry or return behavior and the delegated call shape,
  not Celery internals.
- For a deliberate protocol exception, test the specific behavior that justifies
  it.

## Verification

- targeted `pytest` for the files you touched
- `uv run lint-imports` — a task importing a view breaks the layers contract
- `git diff --check`

## References

- `docs/2-architecture/module-dependencies.rst` — post-commit side effects
- `docs/2-architecture/service-layer.rst` — what stays in the service
- `docs/7-deployment/tiers.rst` — when a project provisions Redis and a worker
- `config/celery_app.py`, and the Celery settings in `config/settings/base.py`
- `.importlinter` — the `(tasks)` optional layer
