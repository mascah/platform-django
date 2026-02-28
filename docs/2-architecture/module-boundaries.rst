Module Boundary Enforcement
===========================

We use static analysis and database design patterns to enforce module boundaries.

Overview
--------

The modular monolith depends on clear boundaries between modules. We enforce these with:

1. **Import enforcement** --- Prevent code in one module from importing internals of another
2. **Database enforcement** --- Prevent direct foreign key relationships between modules

.. note::

   Module boundaries don't mean modules are isolated islands. Valid **one-way dependencies**
   are expected (e.g., ``workflows`` depends on ``organizations``). See :doc:`module-dependencies`
   for when and how to structure these relationships.

Import Enforcement with import-linter
-------------------------------------

`import-linter <https://import-linter.readthedocs.io/>`_ analyzes the import graph and checks it against defined contracts. Configuration is in ``.importlinter`` at the repository root.

Running import-linter
^^^^^^^^^^^^^^^^^^^^^

Check contracts manually::

    uv run lint-imports

This runs in CI and blocks merges on violations.

Contract Types
^^^^^^^^^^^^^^

**Independence contracts** prevent modules from importing each other, even transitively.

**Forbidden contracts** block specific imports (e.g., "orders cannot import user models directly").

**Layers contracts** enforce hierarchical architecture within a module (API -> services -> models).

Violation output looks like:

.. code-block:: text

    BROKEN CONTRACTS:

    No direct cross-module model imports
    ------------------------------------

    platform_django.orders.services -> platform_django.users.models.User (l. 5)

Programmatic Testing with grimp
-------------------------------

For custom architectural rules, use ``grimp`` in pytest:

.. code-block:: python

    # tests/test_architecture.py
    import pytest
    from grimp import build_graph

    @pytest.fixture(scope="session")
    def import_graph():
        return build_graph("platform_django")

    def test_no_circular_dependencies(import_graph):
        modules = ["users", "orders", "billing"]
        for module_a in modules:
            for module_b in modules:
                if module_a != module_b:
                    chain = import_graph.find_shortest_chain(
                        importer=f"platform_django.{module_a}",
                        imported=f"platform_django.{module_b}"
                    )
                    if chain:
                        reverse = import_graph.find_shortest_chain(
                            importer=f"platform_django.{module_b}",
                            imported=f"platform_django.{module_a}"
                        )
                        assert not reverse, f"Circular: {module_a} <-> {module_b}"

Database Boundary Enforcement
-----------------------------

Import boundaries prevent code coupling, but foreign keys create database coupling. When module A has a foreign key to module B's model:

- Module A's tests need module B's data setup (harder to test in isolation)
- Changes to module B's schema can break module A's migrations
- The relationship is implicit---it's not obvious from module A's code that it depends on B

This isn't necessarily bad. For tightly coupled concepts, foreign keys are the right choice. But between truly separate domains, we prefer explicit contracts.

The No-FK Pattern
^^^^^^^^^^^^^^^^^

.. note::

   **Needs team discussion.** This pattern has trade-offs around user permission validation
   and cross-module queries. We should discuss before applying widely.

The pattern: **no foreign keys between modules**. Reference by ID only:

.. code-block:: python

    # platform_django/orders/models.py
    class Order(models.Model):
        user_id = models.IntegerField(db_index=True)  # Not FK
        created_at = models.DateTimeField(auto_now_add=True)
        status = models.CharField(max_length=50)

Cross-module validation happens in services (see :doc:`service-layer` for DTOs and batch fetching patterns):

.. code-block:: python

    # platform_django/orders/services.py
    from platform_django.users.services import user_exists

    def order_create(*, user_id: int, items: list[dict]) -> Order:
        if not user_exists(user_id):
            raise ValidationError("User does not exist")
        return Order.objects.create(user_id=user_id)

Trade-offs
^^^^^^^^^^

**Lost ORM features:**

- No ``select_related()`` across modules
- No ``prefetch_related()`` across modules
- No cascading deletes (handle via events)

**More queries:** Cross-module operations may require additional queries. Mitigate with batch fetching (see :doc:`service-layer`).

**Benefits:**

- True module independence
- Clear ownership of data
- Testable in isolation
- Explicit contracts via service functions

When to Apply
^^^^^^^^^^^^^

Apply between **bounded contexts** --- modules representing different business domains. Within a single module, foreign keys are fine:

.. code-block:: text

    platform_django/
    ├── users/           # FKs within are OK
    │   └── models.py    # User, Profile, UserPreferences interlinked
    ├── orders/          # FKs within are OK
    │   └── models.py    # Order, OrderItem, OrderNote interlinked
    │                    # BUT: Order.user_id is integer, not FK

See Also
--------

- :doc:`/0-introduction/platform-architecture` --- Platform architecture overview
- :doc:`module-structure` --- Creating new modules
- :doc:`module-dependencies` --- Valid dependency patterns between modules
- :doc:`event-driven` --- Cross-module communication without imports
- :doc:`service-layer` --- DTOs and batch fetching
