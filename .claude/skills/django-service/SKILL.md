---
name: django-service
description: Use when adding, changing, or reviewing business writes, create/update/delete operations, transactions, or post-commit side effects under platform_django/.
---

# Django Service

Read the current module and its callers before editing. Preserve the service's
existing return and exception contract unless you are updating every caller and
test together.

## Preflight

Inspect, in order:

- the target service and every current caller
- nearby services in the same module
- tests covering persistence and `transaction.on_commit()`

`platform_django/users/services.py` is the worked example, and
`platform_django/users/views.py` and `api/views.py` are its two callers — one
Django form view, one DRF viewset, both delegating the same write.

## Decide

Use a service for writes under `platform_django/`: create, update, delete,
business mutations, and the orchestration around them.

Prefer `entity_action` names for new public services and selectors. Prefer
keyword-only parameters when a new public operation has two or more inputs.
Treat these as consistency guidance, not findings without a concrete
readability, compatibility, or misuse risk.

Services own writes. Views, serializers, tasks, and webhooks delegate instead of
reimplementing mutation logic. The `api-views-do-not-query` contract in
`.importlinter` fails the build when a query or a save reappears in the API
viewset; nothing catches the same mistake in a form view, so check it yourself.

Use `transaction.atomic()` when coordinating multiple database changes or
registering commit-sensitive side effects. Do not wrap every single-row
mutation by default.

Save an existing row with `update_fields`. A bare `save()` writes every column,
including ones another request changed after this instance was loaded.

Return the same shape callers already expect: model, DTO, primitive, or `None`.
A service called from another module returns primitives or a stable DTO, not an
ORM model.

## Workflow

Keep the service small and explicit:

- validate business preconditions
- perform the write
- update with `update_fields` when saving an existing row
- schedule external side effects only after successful commit

Snapshot stable IDs or other primitives before a commit callback; do not close
over a mutable ORM instance.

```python
order_id = order.pk
transaction.on_commit(lambda: order_confirm_task.delay(order_id))
```

Domain events are not the default answer for ordinary service work. The
template ships no event bus — see `docs/2-architecture/event-driven.rst` before
reaching for one.

## Tests

Add focused service tests near the module for persistence, return and exception
contracts, rollback behavior, and post-commit effects changed by the work. Test
organization should match nearby tests; filenames and class names do not prove
coverage.

Keep these tests narrow: verify the scheduled callback arguments, not Celery
internals. The behavior a caller can observe is asserted at the HTTP seam in
`platform_django/users/tests/api/test_views.py`; the service test exists for
what that seam cannot see cheaply.

## Verification

Run the smallest checks that cover the change:

- targeted `pytest` for the service tests you touched
- `uv run lint-imports` when imports crossed a layer or a module
- `git diff --check`

## Caution

Do not copy the docs literally when code disagrees. Match the current module's
service boundaries, callback scheduling, and caller contracts first.

## References

- `docs/2-architecture/service-layer.rst`
- `docs/2-architecture/module-dependencies.rst` — cross-module calls and
  post-commit dispatch
- `docs/2-architecture/event-driven.rst` — the events decision
- `platform_django/users/services.py` and
  `platform_django/users/tests/test_services.py`
