.. _testing:

Testing
=======

This project uses pytest for all testing. The ``users`` app includes example tests you can reference.

Running Tests
-------------

Run all tests::

    pytest

Run a specific file::

    pytest platform_django/users/tests/test_models.py

Run tests matching a pattern::

    pytest -k "test_user"

With Docker::

    uv run pytest

Isolated Library Tests
^^^^^^^^^^^^^^^^^^^^^^

Libraries in ``libs/`` have their own test suites that run without Django. Use the just commands to run them:

Run tests for all libraries::

    just libs-test

Run tests for a specific library::

    just libs-test-one <name>

Coverage
--------

Run tests with coverage::

    just coverage

This generates both an HTML report and a terminal summary.

Check that coverage meets the minimum threshold (85%)::

    just coverage-check

Open the HTML coverage report in a browser::

    just coverage-report

You can also run coverage manually::

    coverage run -m pytest
    coverage report

Testing Deferred Work
---------------------

Work deferred to ``transaction.on_commit()`` --- queuing a Celery task, calling
an external service --- needs a test that lets the commit happen.

Testing transaction.on_commit()
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Django's ``TestCase`` wraps each test in a transaction that never commits, so
``on_commit()`` callbacks never fire. One way to handle this is
``captureOnCommitCallbacks()``:

.. code-block:: python

    from django.test import TestCase
    from platform_django.orders.services import order_create

    class OrderServiceTests(TestCase):
        def test_confirmation_queued_after_commit(self):
            with self.captureOnCommitCallbacks(execute=True) as callbacks:
                order_create(user_id=1, items=[{"product_id": 1}])

            self.assertEqual(len(callbacks), 1)

With pytest-django, use the ``django_capture_on_commit_callbacks`` fixture:

.. code-block:: python

    import pytest
    from platform_django.orders.services import order_create

    @pytest.mark.django_db
    def test_confirmation_queued(django_capture_on_commit_callbacks):
        with django_capture_on_commit_callbacks(execute=True) as callbacks:
            order_create(user_id=1, items=[{"product_id": 1}])

        assert len(callbacks) == 1

A callback that never fires is the most common cause of a side effect that
works in production and appears untested. For integration tests that need full
transaction behaviour, use ``@pytest.mark.django_db(transaction=True)``.

Test Organization
-----------------

Here's one way to organize tests within a module:

.. code-block:: text

    platform_django/orders/
    ├── tests/
    │   ├── __init__.py
    │   ├── conftest.py        # Module-specific fixtures
    │   ├── factories.py       # Model factories (Factory Boy)
    │   ├── test_models.py     # Model unit tests
    │   ├── test_services.py   # Service layer tests
    │   ├── test_selectors.py  # Selector tests
    │   └── test_api.py        # API endpoint tests

Module fixtures in ``conftest.py``:

.. code-block:: python

    import pytest
    from platform_django.orders.tests.factories import OrderFactory

    @pytest.fixture
    def order(db):
        return OrderFactory()

See Also
--------

- :doc:`/2-architecture/event-driven` — When a boundary justifies domain events
- :doc:`/2-architecture/service-layer` — Testing services and selectors
- :doc:`/2-architecture/module-boundaries` — Architectural testing with grimp
