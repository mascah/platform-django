Module Dependency Patterns
==========================

How modules may depend on each other, and which parts of that are enforced
mechanically.

Overview
--------

Module isolation does not mean zero dependencies. The goal is an acyclic graph,
not a set of islands: a dependency is valid when it points downward, goes
through the callee's public interface, and carries data rather than an ORM
model.

``.importlinter`` is the mechanical gate for the directions encoded in it. That
enforcement is deliberately partial --- it does not prove DTO-only contracts or
post-commit scheduling. See :doc:`module-boundaries`.

Module Levels
-------------

.. list-table::
   :header-rows: 1
   :widths: 22 28 50

   * - Level
     - Modules
     - May depend on
   * - Infrastructure
     - ``core``, ``contrib``
     - Infrastructure only
   * - Foundational
     - ``users``
     - Infrastructure
   * - Feature
     - the modules your project adds
     - Foundational and infrastructure; a dependency between two feature
       modules must be declared explicitly

The template ships the first two levels. A prototype is expected to run on
``core``, ``users`` and one module of its own, so the feature level starts
empty and stays that way until your project has a second bounded context worth
separating.

**The rule**: a higher-level module may depend on a lower-level one, never the
reverse.

Cross-Module Calls
------------------

A direct downward call is the established pattern. The direction is what makes
it valid.

- Call the callee's ``services.py`` for a write and ``selectors.py`` for a
  read.
- Return primitives or a stable DTO, not an ORM model or a ``QuerySet``.
- Import the module's public functions, not its internals. Importing another
  module's models makes every field a de facto public API and defeats the
  boundary.

.. code-block:: python

    # platform_django/orders/services.py  (feature level)
    from platform_django.users.selectors import user_profile_get

    def order_place(*, owner_id: int, items: list[dict]) -> Order:
        profile = user_profile_get(user_id=owner_id)  # downward, returns a DTO
        return Order.objects.create(
            owner_id=owner_id,
            contact_email=profile.email,
        )

Side Effects
------------

Work that must happen only after a successful write is scheduled from
``transaction.on_commit()``, and anything asynchronous or retryable goes to
Celery:

.. code-block:: python

    def order_place(*, owner_id: int, items: list[dict]) -> Order:
        with transaction.atomic():
            order = Order.objects.create(owner_id=owner_id)
            order_id = order.pk  # snapshot a primitive, not the instance
            transaction.on_commit(lambda: order_confirm_task.delay(order_id))
        return order

Capture stable primitives into the callback. Closing over a mutable ORM
instance schedules whatever that object happens to hold when the callback runs,
which is not necessarily what was committed.

Upward or Lateral Communication
-------------------------------

There is no downward call available when a lower-level module needs to notify a
higher-level one, or when two modules at the same level need to react to each
other. The import contracts reject the import, and they are right to.

Resolve it in this order:

#. **Move the behaviour up.** The reaction usually belongs to the higher-level
   module, which may already call downward for the data it needs.
#. **Extract a lower-level module** that both can depend on, when two lateral
   modules share a concern neither owns.
#. **Adopt events** --- last, and deliberately. The template ships no event bus;
   :doc:`event-driven` states the three boundaries that justify one and the
   six-item checklist an adoption must answer first.

Domain events are candidate architecture, not a default. They are not required
for a valid downward dependency, and code written against a bus that does not
exist is code that does not run.

Decision Summary
----------------

+-------------------------+------------------------------------------------+
| Scenario                | Pattern                                        |
+=========================+================================================+
| Need data or behaviour  | Direct downward call: selector for a read,     |
| from a lower module     | service for a write. Return a DTO.             |
+-------------------------+------------------------------------------------+
| Lower module needs to   | Move the behaviour up, or extract a shared     |
| notify a higher one     | lower-level module.                            |
+-------------------------+------------------------------------------------+
| Fire-and-forget side    | Celery task queued from ``on_commit()`` by the |
| effect                  | owning module's service.                       |
+-------------------------+------------------------------------------------+
| Three or more modules   | Justify events against the adoption checklist  |
| react to one occurrence | in :doc:`event-driven`.                        |
+-------------------------+------------------------------------------------+

Anti-Patterns
-------------

**Lower module importing from higher.** Move the aggregation to a higher-level
module that may call both.

**Returning ORM models across a boundary.** Return a DTO; the model's fields
are not a contract.

**Reaching around the public interface.** Importing another module's models to
run your own query bypasses its access scoping, which is the thing its
selectors exist to apply.

See Also
--------

- :doc:`module-boundaries` --- What the contracts prove, and what they do not
- :doc:`service-layer` --- Writing the services and selectors being called
- :doc:`module-structure` --- Creating a new module
- :doc:`event-driven` --- When a boundary justifies domain events
