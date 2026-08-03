---
name: django-test
description: Use when adding, changing, or reviewing pytest coverage for Django services, selectors, APIs, transactions, factories, Celery dispatch, or database behavior under platform_django/.
---

# Django Test

Current code wins over stale docs. Start by reading the code under test and the
nearest live tests in the same module before you write anything.

## Preflight

- Read the service, selector or view you are changing.
- Read nearby tests in the same module. `platform_django/users/tests/` is the
  worked example and carries every shape below.
- Reuse existing factories, fixtures, and assertion style before adding
  anything new. The global `user` fixture lives in `platform_django/conftest.py`.

## Choose the test shape

- Prefer the HTTP seam. `platform_django/users/tests/api/test_views.py` drives
  DRF's `APIClient` and `test_views.py` drives Django's test client; neither
  imports `services` or `selectors`, so both survive logic moving between a view
  and a service. A test that constructs a view instance and calls
  `get_queryset()` or `form_valid()` is coupled to the method whose body is
  about to move.
- Database access: use `@pytest.mark.django_db`. Use
  `@pytest.mark.django_db(transaction=True)` only when the behavior truly
  depends on real transaction boundaries or immediate `on_commit` execution.
- For APIs, assert the status code *and* the persisted state.
- For selectors, assert returned data and the access scope, including that
  another user's row is absent.
- For services, assert the state change and the outward effect, not helper
  internals.
- For a field that must not be writable, attempt the write and assert it did not
  land.

Evaluate coverage by observable behavior and risk. A focused test should prove
the changed success path, the relevant failure or permission path, persisted
state, and outward effect. Follow nearby test organization, but do not infer
coverage from a filename, a class name, or a one-file-per-operation layout.

## Deliberately redundant tests

`users/tests/test_services.py` and `test_selectors.py` duplicate coverage the
HTTP tests already provide. They are marked as reference patterns and should not
be deleted as redundant: the skills tell agents to write focused service and
selector tests, and a reference implementation that contradicts the written
guidance is worse than a little duplication.

## `on_commit` and Celery

Use `django_capture_on_commit_callbacks(execute=True)`. Patch the callback
target at the use site, not where it was originally defined. Assert it is not
called before the block exits, then assert the exact stable arguments after it.

```python
@pytest.mark.django_db
def test_schedules_confirmation(django_capture_on_commit_callbacks):
    with patch.object(order_confirm_task, "delay") as mock_delay:
        with django_capture_on_commit_callbacks(execute=True):
            order = order_place(owner_id=user.pk, items=[])
            mock_delay.assert_not_called()

    mock_delay.assert_called_once_with(order.pk)
```

Test observable behavior. Do not assert callback counts or Celery internals, and
do not write tests against an event bus — the template ships none.

## Isolated libs

Packages under `libs/` are tested without Django: no `@pytest.mark.django_db`,
no Django imports. Run them with `just libs-test` or `just libs-test-one <name>`.

## Verify

- Run the exact case first:
  `pytest platform_django/<module>/tests/test_services.py -k <name>`
- Then the containing file.
- Widen only after the focused case passes. `just coverage-check` enforces the
  85% threshold.

## References

- `docs/3-backend-guides/testing.rst`
- `docs/2-architecture/service-layer.rst` — what services and selectors promise
- `platform_django/users/tests/` — factories, fixtures, HTTP-seam tests, and the
  reference service and selector tests
- `platform_django/conftest.py` — global fixtures
