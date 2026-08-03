---
name: django-selector
description: Use when adding, changing, or reviewing read operations, query functions, list/detail lookups, eager loading, or access-scoped retrieval under platform_django/.
---

# Django Selector

Read the current module before editing. Current code and tests win when older
docs describe a target architecture instead.

## Preflight

Inspect, in order:

- the target selector and every caller
- the serializer or response shape that consumes it
- the module's access-scoped base query, if any
- nearby selector and API tests

`platform_django/users/selectors.py` is the worked example: one access-scoped
base query, consumed by the viewset's `get_queryset`.

Keep selectors read-only: no writes, no externally visible side effects, no task
dispatch.

Preserve the contract callers already rely on:

- return shape: model, `QuerySet`, or DTO
- missing-result behavior: `None`, model `DoesNotExist`, or a selector-specific
  `NotFoundError`

## Decide

Use a selector when the change is a read path under `platform_django/`.

Prefer `entity_action` names for new public services and selectors. Prefer
keyword-only parameters when a new public operation has two or more inputs.
Treat these as consistency guidance, not findings without a concrete
readability, compatibility, or misuse risk.

For lists and paginator/filter inputs, return a `QuerySet` so pagination and
filtering happen in the database. Order it. An unordered queryset behind
`LIMIT`/`OFFSET` skips and duplicates rows between pages.

For detail lookups, keep the current module pattern and preserve the existing
return shape callers use. For a new cross-module selector API, return
primitives or a stable DTO rather than leaking an ORM model or `QuerySet`
across the boundary.

For access-scoped retrieval, start from the scoped base query and fetch from
that queryset. That keeps unauthorized and not-found behavior aligned with
current callers instead of adding a second, different permission path later.

```python
def order_get(*, order_id: int, fetched_by_id: int) -> Order:
    return order_list(fetched_by_id=fetched_by_id).get(id=order_id)
```

Add relationship loading only for data the current serializer or caller actually
touches. Use `select_related` and `prefetch_related` from the concrete read
path; do not preload relationships speculatively.

Use `only` or `defer` separately for column projection, and preserve every field
the caller or serializer needs.

## Tests

Add focused selector tests near the module for the access scope, missing-result
contract, return shape, and query behavior changed. Test organization should
match nearby tests; filenames and class names do not prove coverage.

Keep tests narrow. A selector test should prove the read contract, not service
behavior. `platform_django/users/tests/test_selectors.py` asserts the access
scope — that another user's row is absent, not merely that the query returns.

## Verification

Run the smallest checks that cover the change:

- targeted `pytest` for the selector tests you touched
- `uv run lint-imports` — a selector importing a service breaks the layers
  contract
- `git diff --check`

## Caution

Do not invent DTO layers or new abstractions because a doc mentions them. Match
the current module first, then change architecture only when the surrounding
code already supports it.

## References

- `docs/2-architecture/service-layer.rst`
- `docs/2-architecture/module-dependencies.rst` — what a cross-module read
  returns
- `platform_django/users/selectors.py` and
  `platform_django/users/tests/test_selectors.py`
