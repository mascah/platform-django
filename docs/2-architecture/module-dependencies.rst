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
- ``domain_events`` --- Event bus infrastructure

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

When you need "reverse" communication---a lower-level module notifying a higher-level one---use domain events instead of imports. This breaks the cycle.

Communication Patterns
----------------------

Two patterns exist for cross-module communication, and the choice depends on **direction**.

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

Asynchronous: Domain Events (Upward or Lateral)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When a lower-level module needs to notify higher-level modules about something that happened, emit an event:

.. code-block:: python

    # platform_django/organizations/services.py
    from django.db import transaction
    from platform_django.domain_events.bus import event_bus
    from platform_django.domain_events.events import OrganizationConfigChangedEvent

    def organization_update_config(*, org_id: int, **updates) -> OrganizationConfigDTO:
        """Update org config and notify subscribers."""
        with transaction.atomic():
            org = Organization.objects.get(id=org_id)
            for key, value in updates.items():
                setattr(org, key, value)
            org.save()

            # Notify via event --- NOT by importing workflows
            def _publish():
                event_bus.publish(OrganizationConfigChangedEvent(org_id=org.id))
            transaction.on_commit(_publish)

        return organization_get_config(org_id=org_id)

The ``workflows`` module subscribes to this event without ``organizations`` needing to know about it:

.. code-block:: python

    # platform_django/workflows/apps.py
    from django.apps import AppConfig

    class WorkflowsConfig(AppConfig):
        name = "platform_django.workflows"

        def ready(self) -> None:
            from platform_django.domain_events.bus import event_bus
            from platform_django.domain_events.events import OrganizationConfigChangedEvent
            from platform_django.workflows.handlers import handle_org_config_changed

            event_bus.subscribe(OrganizationConfigChangedEvent, handle_org_config_changed)

**This pattern enables bidirectional communication without circular dependencies:**

.. code-block:: text

    workflows                       organizations
    +--------+                      +------------+
    |        |                      |            |
    |   -------- service call ------->           |  (sync, returns DTO)
    |        |                      |            |
    |   <-------- domain event -----             |  (async, via event bus)
    +--------+                      +------------+

Decision Framework
------------------

Use this flowchart to decide between service calls and domain events:

.. code-block:: text

    Need to communicate between modules?
           |
           v
    Does caller need an immediate response?
           |
           +---- YES --> Is caller higher-level than callee?
           |                  |
           |                  +---- YES --> Use service call returning DTO
           |                  |
           |                  +---- NO  --> STOP! This creates a circular dep.
           |                               Refactor: callee emits event,
           |                               caller subscribes
           |
           +---- NO --> Use domain event (any direction is fine)

**Summary:**

+-------------------+---------------------------+---------------------------+
| Scenario          | Pattern                   | Example                   |
+===================+===========================+===========================+
| Need data from    | Service call returning    | ``workflows`` calls       |
| lower-level       | DTO                       | ``organizations``         |
| module            |                           | ``.get_config()``         |
+-------------------+---------------------------+---------------------------+
| Lower module      | Domain event              | ``organizations`` emits   |
| needs to notify   |                           | ``ConfigChangedEvent``    |
| higher modules    |                           |                           |
+-------------------+---------------------------+---------------------------+
| Multiple modules  | Domain event              | ``orders`` emits          |
| react to same     |                           | ``OrderPlacedEvent``,     |
| occurrence        |                           | billing + fulfillment     |
|                   |                           | both handle               |
+-------------------+---------------------------+---------------------------+
| Fire-and-forget   | Domain event              | Any audit logging,        |
| side effects      |                           | analytics, notifications  |
+-------------------+---------------------------+---------------------------+

Worked Example: Organizations and Workflows
-------------------------------------------

This example demonstrates the complete pattern for two modules with a valid one-way dependency.

**Module structure:**

.. code-block:: text

    platform_django/
    ├── organizations/
    │   ├── models.py           # Organization model
    │   ├── services.py         # Public API with DTOs
    │   └── events.py           # Events this module emits
    └── workflows/
        ├── models.py           # Workflow model (references org by ID)
        ├── services.py         # Imports from organizations.services
        ├── handlers.py         # Handles events from organizations
        └── apps.py             # Registers event handlers

**The organizations module's public interface:**

.. code-block:: python

    # platform_django/organizations/services.py
    from dataclasses import dataclass
    from django.db import transaction
    from platform_django.domain_events.bus import event_bus
    from platform_django.organizations.models import Organization
    from platform_django.organizations.events import OrganizationConfigChangedEvent

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

        Emits OrganizationConfigChangedEvent so dependent modules can react.
        """
        with transaction.atomic():
            org = Organization.objects.select_for_update().get(id=org_id)

            if workflow_settings is not None:
                org.workflow_settings = workflow_settings
            if feature_flags is not None:
                org.feature_flags = feature_flags
            org.save()

            # Emit event for subscribers (like workflows module)
            def _publish():
                event_bus.publish(OrganizationConfigChangedEvent(org_id=org.id))
            transaction.on_commit(_publish)

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

**The workflows module reacting to organization changes:**

.. code-block:: python

    # platform_django/workflows/handlers.py
    import logging
    from platform_django.organizations.events import OrganizationConfigChangedEvent
    from platform_django.organizations.services import organization_get_config
    from platform_django.workflows.models import Workflow

    logger = logging.getLogger(__name__)

    def handle_org_config_changed(event: OrganizationConfigChangedEvent) -> None:
        """
        React to organization configuration changes.

        Updates workflow defaults when org settings change.
        """
        config = organization_get_config(org_id=event.org_id)
        new_defaults = config.workflow_settings.get("defaults", {})

        # Update workflows that use org defaults
        updated = Workflow.objects.filter(
            organization_id=event.org_id,
            uses_org_defaults=True,
        ).update(settings=new_defaults)

        logger.info(
            "Updated %d workflows for org %d after config change",
            updated,
            event.org_id,
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
        platform_django.domain_events

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

**Fix**: Have ``organizations`` emit an event, or move the stats aggregation to a higher-level module.

**Anti-pattern 2: Returning ORM models across module boundaries**

.. code-block:: python

    # BAD: organizations/services.py
    def organization_get(org_id: int) -> Organization:  # Leaks internal model
        return Organization.objects.get(id=org_id)

**Fix**: Return a DTO instead. This keeps the internal model structure hidden.

**Anti-pattern 3: Circular event handlers**

.. code-block:: python

    # BAD: Creates implicit circular dependency via events
    # organizations emits ConfigChanged -> workflows handles it and emits WorkflowUpdated
    # -> organizations handles WorkflowUpdated and emits ConfigChanged again

**Fix**: Events should not trigger chains that loop back. If you find yourself in this situation, reconsider the module boundaries.

See Also
--------

- :doc:`module-boundaries` --- Enforcing boundaries with import-linter
- :doc:`service-layer` --- Service/selector pattern and DTOs
- :doc:`event-driven` --- Domain events and the event bus
- :doc:`module-structure` --- Creating new modules
