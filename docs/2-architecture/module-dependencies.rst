Module Dependency Patterns
==========================

When and how modules can legitimately depend on each other.

Overview
--------

Module isolation doesn't mean zero dependencies. The goal is an **Acyclic Dependency Graph (DAG)**, not isolated islands.

Valid dependencies exist when:

- A higher-level module needs data or behavior from a lower-level module
- The dependency flows in one direction only
- Communication uses explicit interfaces (service functions returning DTOs)

Invalid dependencies create:

- Circular imports (A imports B, B imports A)
- Tight coupling to internal implementation details
- Difficulty testing modules in isolation

The Module Hierarchy
--------------------

Modules form a hierarchy of abstraction levels:

.. code-block:: text

        +-----------------+     +-----------------+
        |   workflows     |     |     orders      |   <- Feature tier
        +--------+--------+     +--------+--------+
                 |                       |
                 v                       v
        +--------+--------+     +--------+--------+
        | organizations   |     |     users       |   <- Domain core
        +--------+--------+     +--------+--------+
                 |                       |
                 +----------+------------+
                            |
                            v
                 +----------+----------+
                 |    core / infra     |            <- Infrastructure
                 +---------------------+

**Infrastructure tier** (lowest level):

- ``core`` --- Shared utilities, base models, common functionality

**Domain Core tier** (middle level):

- ``users`` --- User management, authentication
- ``organizations`` --- Tenant configuration, org-level settings

**Feature tier** (highest level):

- ``workflows`` --- Business process automation
- ``orders`` --- Order processing and fulfillment
- ``billing`` --- Subscription and payment handling

**The rule**: Higher-level modules can depend on lower-level modules, never the reverse.

The Acyclic Dependencies Principle
----------------------------------

Dependencies must form a Directed Acyclic Graph (DAG):

.. code-block:: text

    Valid:                          Invalid:

    workflows -> organizations      workflows -> organizations
                                          ^            |
                                          |            v
                                          +--- orders -+

**Valid**: ``workflows`` depends on ``organizations`` (one-way)

**Invalid**: ``workflows`` depends on ``organizations``, and ``orders`` depends on ``workflows``, and ``organizations`` depends on ``orders`` (cycle)

A dependency that wants to point upward is a design signal. Move the behaviour to the higher-level module, or---if the boundary genuinely warrants it---adopt events against the checklist in :doc:`event-driven`.

Communication Patterns
----------------------

Cross-module communication is a direct downward call. The direction is what makes it valid.

Synchronous: Service Calls (Downward)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When a higher-level module needs data or behavior from a lower-level module, use direct service calls:

.. code-block:: python

    # platform_django/workflows/services.py
    from platform_django.organizations.services import organization_get_config

    def workflow_create(*, org_id: int, name: str) -> Workflow:
        """Create a workflow using org configuration."""
        config = organization_get_config(org_id=org_id)  # Valid: downward call
        return Workflow.objects.create(
            organization_id=org_id,
            name=name,
            settings=config.workflow_settings,
        )

**Requirements for service calls across modules:**

- The called service must return a **DTO** (dataclass or Pydantic model), not an ORM model
- The caller must be at a higher abstraction level than the callee
- Document which services are part of the module's public API

Upward or Lateral Communication
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

Decision Framework
------------------

Use this flowchart to decide how one module reaches another:

.. code-block:: text

    Need to communicate between modules?
           |
           v
    Is the caller higher-level than the callee?
           |
           +---- YES --> Service call for a write, selector for a read.
           |             Return a DTO, not an ORM model.
           |
           +---- NO  --> STOP. A direct import here creates a cycle.
                         Move the behaviour up, or extract a shared
                         lower-level module. If neither fits, see
                         event-driven for the events decision.

**Summary:**

+-------------------+---------------------------+---------------------------+
| Scenario          | Pattern                   | Example                   |
+===================+===========================+===========================+
| Need data from    | Service call returning    | ``workflows`` calls       |
| lower-level       | DTO                       | ``organizations``         |
| module            |                           | ``.get_config()``         |
+-------------------+---------------------------+---------------------------+
| Lower module      | Move the behaviour to the | ``workflows`` reads org   |
| needs to notify   | higher module, or extract | config on its own         |
| higher modules    | a shared lower one        | schedule                  |
+-------------------+---------------------------+---------------------------+
| Fire-and-forget   | Celery task queued by the | Audit logging queued in   |
| side effects      | owning module's service   | the service that wrote    |
+-------------------+---------------------------+---------------------------+
| Three or more     | Justify events against    | See :doc:`event-driven`   |
| modules react to  | the adoption checklist    |                           |
| one occurrence    |                           |                           |
+-------------------+---------------------------+---------------------------+

Worked Example: Organizations and Workflows
-------------------------------------------

This example demonstrates the complete pattern for two modules with a valid one-way dependency.

**Module structure:**

.. code-block:: text

    platform_django/
    ├── organizations/
    │   ├── models.py           # Organization model
    │   ├── services.py         # Public API for writes, returns DTOs
    │   └── selectors.py        # Public API for reads, returns DTOs
    └── workflows/
        ├── models.py           # Workflow model (references org by ID)
        └── services.py         # Imports from organizations.services

**The organizations module's public interface:**

.. code-block:: python

    # platform_django/organizations/services.py
    from dataclasses import dataclass
    from django.db import transaction
    from platform_django.organizations.models import Organization

    @dataclass(frozen=True)
    class OrganizationConfigDTO:
        """Data transfer object for organization configuration."""
        id: int
        name: str
        workflow_settings: dict
        feature_flags: dict

    # === PUBLIC API ===

    def organization_get_config(*, org_id: int) -> OrganizationConfigDTO:
        """
        Get organization configuration.

        This is part of the public API for cross-module use.
        Returns a DTO, not the ORM model.
        """
        org = Organization.objects.get(id=org_id)
        return OrganizationConfigDTO(
            id=org.id,
            name=org.name,
            workflow_settings=org.workflow_settings,
            feature_flags=org.feature_flags,
        )

    def organization_update_config(
        *,
        org_id: int,
        workflow_settings: dict | None = None,
        feature_flags: dict | None = None,
    ) -> OrganizationConfigDTO:
        """
        Update organization configuration.

        Callers that need the new values read them through
        organization_get_config.
        """
        with transaction.atomic():
            org = Organization.objects.select_for_update().get(id=org_id)

            if workflow_settings is not None:
                org.workflow_settings = workflow_settings
            if feature_flags is not None:
                org.feature_flags = feature_flags
            org.save()

        return organization_get_config(org_id=org_id)

**The workflows module consuming the interface:**

.. code-block:: python

    # platform_django/workflows/services.py
    from platform_django.organizations.services import organization_get_config
    from platform_django.workflows.models import Workflow

    def workflow_create(*, org_id: int, name: str, steps: list[dict]) -> Workflow:
        """
        Create a new workflow for an organization.

        Uses organization config to apply org-level defaults.
        """
        config = organization_get_config(org_id=org_id)

        # Apply org-level workflow settings as defaults
        default_settings = config.workflow_settings.get("defaults", {})

        return Workflow.objects.create(
            organization_id=org_id,  # Integer reference, not FK
            name=name,
            steps=steps,
            settings={**default_settings},
        )

Enforcing with import-linter
----------------------------

Use ``import-linter`` layers contracts to enforce the module hierarchy:

.. code-block:: ini

    # .importlinter

    [importlinter]
    root_package = platform_django

    # Enforce module hierarchy
    [importlinter:contract:module-hierarchy]
    name = Module hierarchy is respected
    type = layers
    layers =
        # Feature tier (can import from domain core and infrastructure)
        platform_django.workflows
        platform_django.orders
        platform_django.billing
        # Domain core (can import from infrastructure only)
        platform_django.organizations
        platform_django.users
        # Infrastructure (cannot import from higher levels)
        platform_django.core

With this configuration, ``import-linter`` will fail if:

- ``organizations`` tries to import from ``workflows`` (lower importing higher)
- ``core`` tries to import from ``users`` (infrastructure importing domain core)

Run the check with::

    uv run lint-imports

See :doc:`module-boundaries` for more on import-linter configuration.

Common Anti-Patterns
--------------------

**Anti-pattern 1: Lower module importing from higher**

.. code-block:: python

    # BAD: organizations/services.py
    from platform_django.workflows.services import workflow_count_for_org  # Wrong direction!

    def organization_get_stats(org_id: int) -> dict:
        return {"workflow_count": workflow_count_for_org(org_id)}

**Fix**: Move the stats aggregation to a higher-level module that may call both.

**Anti-pattern 2: Returning ORM models across module boundaries**

.. code-block:: python

    # BAD: organizations/services.py
    def organization_get(org_id: int) -> Organization:  # Leaks internal model
        return Organization.objects.get(id=org_id)

**Fix**: Return a DTO instead. This keeps the internal model structure hidden.

**Anti-pattern 3: Reaching around the public interface**

.. code-block:: python

    # BAD: workflows/services.py
    from platform_django.organizations.models import Organization  # Internal model

    def workflow_settings_for(org_id: int) -> dict:
        return Organization.objects.get(id=org_id).workflow_settings

**Fix**: Call the lower module's selector. Importing its models makes every
field a de facto public API and defeats the DTO boundary.

See Also
--------

- :doc:`module-boundaries` --- Enforcing boundaries with import-linter
- :doc:`service-layer` --- Service/selector pattern and DTOs
- :doc:`event-driven` --- When a boundary justifies domain events
- :doc:`module-structure` --- Creating new modules
