Module Boundary Enforcement
===========================

What a boundary is checked by, and what still needs review.

Overview
--------

A module boundary is held in two different ways, and the difference matters
more than the rules themselves:

1. **Import enforcement** --- ``.importlinter`` checks dependency directions
   and internal layers on every commit. What it declares, it proves.
2. **Data-model review** --- cross-module relations need ownership and
   integrity judgment that no linter can make for you.

Treat the first as settled and the second as a decision you must state.

Import Enforcement with import-linter
-------------------------------------

`import-linter <https://import-linter.readthedocs.io/>`_ analyses the import
graph and checks it against the contracts in ``.importlinter`` at the
repository root. Run it with::

    uv run lint-imports

It runs in CI and in the pre-commit hook. This is the primary mechanical
architecture gate.

What the shipped contracts assert
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The template ships three contracts, all of them exercised by
``platform_django/users/``:

``infrastructure-isolation``
   ``core`` is the lowest-level module and may not import a business module.
   A new module is added to this contract's ``forbidden_modules``.

``users-internal-layers``
   Within the module, ``api`` and ``views`` may call ``services`` and
   ``selectors``, and never the reverse. A selector that imports a service
   fails the build. ``tasks`` is parenthesised because the module ships no
   Celery task --- an optional layer holds its position in the hierarchy for
   the project that adds one.

``api-views-do-not-query``
   The layers contract gates direction, but it cannot catch a write
   reimplemented inside a view: such a view imports nothing a layers contract
   forbids. This one forbids the API viewset from importing the model at all,
   so a query or a save placed back in it fails. ``allow_indirect_imports``
   keeps the check on the viewset's own code --- reaching the model *through*
   a selector or a serializer is the point of those layers.

Add contracts for a new module as you create it, not afterwards. See
:doc:`module-structure`.

Cross-Module Model Relations
----------------------------

There is no blanket "never use foreign keys across modules" rule. Evaluate
each relation case by case, and record the reason.

A cross-module foreign key needs a stated justification of a particular kind:

- ownership or referential integrity that is best enforced in the database;
- lifecycle coupling tight enough that an integer identifier would lose a
  guarantee the project needs;
- reverse traversal that is actually used.

The list is illustrative, not closed. What is required is a stated reason of
that kind --- ``ForeignKey(settings.AUTH_USER_MODEL)`` recording who owns a
row is the ordinary case, and writing it as a bare integer column surrenders
referential integrity on the relation that most wants it.

Prefer integer identifiers when the two lifecycles are independently owned, or
when a later split of the module matters more than ORM convenience. That bias
is what keeps such a split from becoming a schema migration.

Where a relation is justified but nothing traverses it backwards, declare it
``related_name="+"``:

.. code-block:: python

    class Order(models.Model):
        # Ownership belongs in the database: an order without its user is
        # meaningless, and the cascade is the behaviour we want.
        owner = models.ForeignKey(
            settings.AUTH_USER_MODEL,
            on_delete=models.CASCADE,
            related_name="+",  # nothing reads user.order_set
        )

This is the part most easily forgotten and the part that does the work: it
keeps a justified foreign key from quietly becoming a two-way dependency
through the reverse accessor.

See ADR-0009 for the decision behind this policy.

What import-linter Does Not Prove
---------------------------------

The contracts say nothing about:

- whether a cross-module call returns a DTO or leaks an ORM model;
- whether asynchronous side effects are scheduled after commit;
- whether a foreign key across modules carries a justification.

Those stay review concerns, backed by focused tests, until an executable check
exists for them. A contract that passes is not a design that is correct.

See Also
--------

- :doc:`module-dependencies` --- Which direction a dependency may run
- :doc:`module-structure` --- Creating a new module and its contracts
- :doc:`service-layer` --- Services, selectors and DTOs
- :doc:`event-driven` --- When a boundary justifies domain events
