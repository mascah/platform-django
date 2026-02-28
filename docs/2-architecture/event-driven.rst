Event-Driven Architecture
=========================

Domain events decouple modules by allowing them to communicate without direct imports. This is one approach to cross-module communication---direct service calls are also valid for simpler cases.

Overview
--------

When modules need to communicate, you have two options:

1. **Direct service calls** --- Simple, explicit, good for request/response patterns
2. **Domain events** --- Decoupled, good when multiple modules react to the same occurrence

Events are the right choice when:

- Multiple modules need to react to the same occurrence
- You want to add reactions without modifying the original code
- You're considering extracting modules to separate services

**Use direct service calls when:**

- Only one module needs to react
- The caller needs a return value
- The relationship is unlikely to change

Start with direct calls if unsure. Refactor to events when coupling becomes painful.

When to Introduce Events
^^^^^^^^^^^^^^^^^^^^^^^^^

Domain events add indirection. Before reaching for them, consider whether a simpler approach works:

- **One module reacting to another?** A direct service call is simpler and easier to trace.
- **Two or three modules reacting to the same thing?** Events start to pay off here.
- **Need to decouple a lower-level module from higher-level ones?** Events are the right tool---they let you avoid circular dependencies.

A good rule of thumb: if you find yourself importing from a higher-level module into a lower-level one, that is a signal to use events instead.

Communication Direction
^^^^^^^^^^^^^^^^^^^^^^^

The choice between service calls and events often depends on the **direction** of communication:

- **Downward** (high-level to low-level): Direct service calls are natural. For example, ``workflows`` can call ``organizations.services.get_org_config()``.
- **Upward** (low-level to high-level): Events prevent circular dependencies. For example, ``organizations`` should emit ``OrganizationConfigChangedEvent`` rather than importing from ``workflows``.

This asymmetry is key to maintaining an acyclic dependency graph. See :doc:`module-dependencies` for the complete decision framework and worked examples.

The Event Bus
-------------

At the heart of the system is a simple in-memory event bus that routes events to registered handlers.

.. code-block:: python

    # platform_django/domain_events/bus.py
    from collections import defaultdict

    class EventBus:
        """A simple in-memory pub-sub mechanism for domain events."""

        def __init__(self):
            self._subscribers = defaultdict(list)

        def subscribe(self, event_type, handler):
            """Register a handler for a given event type."""
            self._subscribers[event_type].append(handler)

        def publish(self, event):
            """Publish an event to all registered handlers."""
            event_type = type(event)
            for handler in self._subscribers.get(event_type, []):
                handler(event)

    # Module-level singleton
    event_bus = EventBus()

The event bus is instantiated once at module load time. All modules import the same ``event_bus`` singleton.

Defining Events
---------------

Events are simple data classes that represent something that happened in your domain:

.. code-block:: python

    # platform_django/domain_events/events.py
    from platform_django.domain_events.base import DomainEvent

    class UserCreatedEvent(DomainEvent):
        """Emitted when a new user is created."""

        def __init__(self, user_id: int, email: str):
            self.user_id = user_id
            self.email = email


    class OrderPlacedEvent(DomainEvent):
        """Emitted when a new order is placed."""

        def __init__(
            self,
            order_id: int,
            user_id: int,
            total_amount: int,
        ):
            self.order_id = order_id
            self.user_id = user_id
            self.total_amount = total_amount

**Naming conventions:**

- Use past tense: ``OrderPlacedEvent``, not ``PlaceOrderEvent``
- Include the domain context: ``UserCreatedEvent``, ``OrderPlacedEvent``
- Be specific about what happened

**What data to include:**

- IDs needed to look up related entities
- Key state that handlers need without additional queries
- Avoid including full model instances (they may be stale)

Registering Handlers
--------------------

Handlers are registered during Django's app initialization using ``AppConfig.ready()``:

.. code-block:: python

    # platform_django/notifications/apps.py
    from django.apps import AppConfig

    class NotificationsConfig(AppConfig):
        name = "platform_django.notifications"
        verbose_name = "Notifications"

        def ready(self) -> None:
            """Register event handlers when the app is ready."""
            from platform_django.domain_events.bus import event_bus
            from platform_django.domain_events.events import (
                UserCreatedEvent,
                OrderPlacedEvent,
            )
            from platform_django.notifications.handlers import (
                handle_user_created,
                handle_order_placed,
            )

            event_bus.subscribe(
                UserCreatedEvent,
                handle_user_created,
            )
            event_bus.subscribe(
                OrderPlacedEvent,
                handle_order_placed,
            )

**Key points:**

- Use lazy imports inside ``ready()`` to avoid circular dependencies
- Handlers can be functions or class methods
- Multiple handlers can subscribe to the same event type

Handler Implementation
^^^^^^^^^^^^^^^^^^^^^^

Handlers receive the event and perform their logic:

.. code-block:: python

    # platform_django/notifications/handlers.py
    import logging
    from platform_django.domain_events.events import OrderPlacedEvent

    logger = logging.getLogger(__name__)

    def handle_order_placed(event: OrderPlacedEvent) -> None:
        """Send a confirmation notification when an order is placed."""
        logger.info(
            "Sending order confirmation for order %d to user %d",
            event.order_id,
            event.user_id,
        )
        # Send email, push notification, etc.
        send_order_confirmation_email.delay(
            order_id=event.order_id,
            user_id=event.user_id,
        )

Publishing Events Safely
------------------------

.. warning::

   **Critical: Never publish events before the transaction commits.**

   This is the most common bug in event-driven systems. If you publish before commit and the
   transaction rolls back, handlers will process an event for data that doesn't exist. This causes:

   - Handlers that fail with "object not found" errors
   - Inconsistent state between modules
   - Hard-to-debug race conditions

   **Always use** ``transaction.on_commit()`` **to publish events.**

Use Django's ``transaction.on_commit()``:

.. code-block:: python

    # platform_django/orders/services.py
    from django.db import transaction
    from platform_django.domain_events.bus import event_bus
    from platform_django.domain_events.events import OrderPlacedEvent

    @transaction.atomic
    def order_create(*, user_id: int, items: list[dict]) -> "Order":
        """Create an order and notify subscribers."""
        order = Order.objects.create(user_id=user_id, status="pending")
        total = 0
        for item in items:
            order_item = OrderItem.objects.create(order=order, **item)
            total += order_item.price * order_item.quantity

        order.total_amount = total
        order.save()

        # CRITICAL: Publish event ONLY after transaction commits
        def _publish_event():
            event = OrderPlacedEvent(
                order_id=order.id,
                user_id=user_id,
                total_amount=total,
            )
            event_bus.publish(event)

        transaction.on_commit(_publish_event)

        return order

**What happens:**

1. Database changes are made within the ``@transaction.atomic`` block
2. ``transaction.on_commit(_publish_event)`` registers the callback
3. When the transaction commits successfully, Django calls ``_publish_event()``
4. The event is published and handlers execute
5. If the transaction rolls back, the callback is never called

Django Signals vs Domain Events
-------------------------------

Django provides built-in signals (``pre_save``, ``post_save``, etc.). When should you use them vs domain events?

**Use Django signals for:**

- Model lifecycle hooks within a single module
- Auditing changes, updating timestamps
- Clearing caches when a model changes

**Use domain events for:**

- Cross-module communication
- Business domain concepts that represent meaningful occurrences
- Explicit contracts between modules
- Functionality you might extract to a separate service

**Key differences:**

+------------------------+------------------+---------------------------+
| Aspect                 | Django Signals   | Domain Events             |
+========================+==================+===========================+
| Coupling               | Model-level      | Domain-level              |
+------------------------+------------------+---------------------------+
| Scope                  | Within Django    | Cross-module              |
+------------------------+------------------+---------------------------+
| Contract               | Implicit         | Explicit event classes    |
+------------------------+------------------+---------------------------+
| Extractability         | Hard             | Easy (change transport)   |
+------------------------+------------------+---------------------------+

Scaling the Event Bus
---------------------

The in-memory event bus handles most applications. When you need to scale beyond a single process, you can swap in an external broker.

**When in-memory works:**

- Your application runs as a single process (or multiple identical processes)
- Event handlers are fast and don't need independent scaling
- You don't need event persistence or replay

**When to consider external brokers:**

- You need to scale event consumers independently
- Events should persist if the application restarts
- You're extracting a module to a separate service
- You need guaranteed delivery with acknowledgment

**Migration path:**

1. Define an abstract interface for the event bus
2. Create a new implementation that publishes to RabbitMQ/SNS
3. Swap the implementation via configuration
4. Event classes remain unchanged---they're just serialized differently

Summary
-------

1. **Start simple**: Use direct service calls first; introduce events when multiple modules need to react or when you need to break circular dependencies
2. **Event Bus Singleton**: Single registry of subscribers, imported everywhere
3. **Events as Data Classes**: Simple classes representing domain occurrences
4. **Register in AppConfig.ready()**: Lazy imports, wired at startup
5. **Publish with transaction.on_commit()**: Never publish before data is committed
6. **Domain Events > Django Signals**: For cross-module communication
7. **Scalability Path**: Same contracts work with external brokers when needed
