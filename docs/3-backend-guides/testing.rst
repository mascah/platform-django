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

    docker compose run --rm django pytest

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

Testing Event-Driven Code
--------------------------

The event-driven architecture (see :doc:`/2-architecture/event-driven`) needs specific testing patterns because events are published inside ``transaction.on_commit()`` callbacks.

Testing transaction.on_commit()
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Django's ``TestCase`` wraps each test in a transaction that never commits, so ``on_commit()`` callbacks never fire. One way to handle this is ``captureOnCommitCallbacks()``:

.. code-block:: python

    from django.test import TestCase
    from platform_django.orders.services import order_create

    class OrderServiceTests(TestCase):
        def test_event_published_after_commit(self):
            with self.captureOnCommitCallbacks(execute=True) as callbacks:
                order = order_create(user_id=1, items=[{"product_id": 1}])

            self.assertEqual(len(callbacks), 1)

With pytest-django, use the ``django_capture_on_commit_callbacks`` fixture:

.. code-block:: python

    import pytest
    from platform_django.orders.services import order_create

    @pytest.mark.django_db
    def test_event_published(django_capture_on_commit_callbacks):
        with django_capture_on_commit_callbacks(execute=True) as callbacks:
            order = order_create(user_id=1, items=[{"product_id": 1}])

        assert len(callbacks) == 1

For integration tests that need full transaction behavior, use ``@pytest.mark.django_db(transaction=True)``.

The FakeEventBus Pattern
^^^^^^^^^^^^^^^^^^^^^^^^

If you want to test event handlers in isolation, a test double can help:

.. code-block:: python

    # platform_django/domain_events/testing.py
    from typing import Type

    class FakeEventBus:
        """Test double that captures events without handling them."""

        def __init__(self):
            self.published_events = []
            self._subscribers = {}

        def publish(self, event):
            self.published_events.append(event)

        def subscribe(self, event_type, handler):
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(handler)

        def assert_event_published(self, event_type: Type, **attrs):
            for event in self.published_events:
                if isinstance(event, event_type):
                    if all(getattr(event, k, None) == v for k, v in attrs.items()):
                        return True
            raise AssertionError(
                f"Event {event_type.__name__} with {attrs} not found. "
                f"Published: {[type(e).__name__ for e in self.published_events]}"
            )

        def clear(self):
            self.published_events.clear()

Using the FakeEventBus:

.. code-block:: python

    import pytest
    from unittest.mock import patch
    from platform_django.domain_events.testing import FakeEventBus
    from platform_django.domain_events.events import OrderCreatedEvent
    from platform_django.orders.services import order_create

    @pytest.fixture
    def fake_event_bus():
        bus = FakeEventBus()
        with patch("platform_django.domain_events.bus.event_bus", bus):
            yield bus

    @pytest.mark.django_db
    def test_order_create_publishes_event(fake_event_bus, django_capture_on_commit_callbacks):
        with django_capture_on_commit_callbacks(execute=True):
            order = order_create(user_id=42, items=[{"product_id": 1}])

        fake_event_bus.assert_event_published(
            OrderCreatedEvent,
            order_id=order.id,
            user_id=42,
        )

Contract Testing with Pydantic
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Domain events form contracts between modules. Use Pydantic to catch breaking changes:

.. code-block:: python

    from pydantic import BaseModel, ConfigDict

    class OrderCreatedEventContract(BaseModel):
        model_config = ConfigDict(extra="forbid")

        order_id: int
        user_id: int
        items: list[dict]
        total_amount: str

Test that events match contracts:

.. code-block:: python

    def test_order_created_event_matches_contract():
        event = OrderCreatedEvent(
            order_id=1,
            user_id=42,
            items=[{"product_id": 1, "quantity": 2}],
            total_amount="99.99",
        )

        # Raises ValidationError if event doesn't match
        OrderCreatedEventContract(
            order_id=event.order_id,
            user_id=event.user_id,
            items=event.items,
            total_amount=event.total_amount,
        )

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
    │   ├── test_handlers.py   # Event handler tests
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

- :doc:`/2-architecture/event-driven` — Event bus and transaction.on_commit() patterns
- :doc:`/2-architecture/service-layer` — Testing services and selectors
- :doc:`/2-architecture/module-boundaries` — Architectural testing with grimp
