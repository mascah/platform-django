Adding Modules to the Modular Monolith
======================================

This documents how to add new modules (Django apps). Each module represents a bounded domain context.

Overview
--------

We're organizing the application into **modules**: self-contained Django apps that encapsulate specific business domains. Unlike microservices, these modules run in the same process and share a database, but we're aiming to maintain clear boundaries through explicit interfaces.

For an overview of how the codebase is organized, see :doc:`/0-introduction/platform-architecture`.

Project Layout
--------------

We're using the "Two Scoops of Django" layout with a two-tier structure:

- **Top Level Repository Root** has config files, documentation, ``manage.py``, and more.
- **Second Level Django Project Root** (``platform_django/``) is where your modules live.
- **Second Level Configuration Root** (``config/``) holds settings and URL configurations.

The project layout::

    platform-django/
    ├── config/
    │   ├── settings/
    │   │   ├── __init__.py
    │   │   ├── base.py
    │   │   ├── local.py
    │   │   └── production.py
    │   ├── urls.py
    │   └── wsgi.py
    ├── platform_django/              # Modular monolith container
    │   ├── users/                 # User management module
    │   ├── core/                  # Shared utilities and base models
    │   ├── domain_events/         # Event bus infrastructure
    │   └── <your_new_module>/     # Add new modules here
    ├── manage.py
    ├── README.md
    └── ...

The ``platform_django/`` directory is the **modular monolith container**. Each subdirectory is a module (Django app) representing a distinct business domain.

Creating a New Module
---------------------

Follow these steps to add a new module:

#. **Create the app** using Django's ``startapp`` command::

    python manage.py startapp <module_name>

#. **Move the app** to the Django Project Root::

    mv <module_name> platform_django/

#. **Edit the app's apps.py** to update the module path. Change::

    name = '<module_name>'

   To::

    name = 'platform_django.<module_name>'

#. **Register the module** in ``config/settings/base.py``::

    LOCAL_APPS = [
        "platform_django.users",
        "platform_django.core",
        "platform_django.domain_events",
        "platform_django.<module_name>",  # Add your new module
    ]

#. **Run migrations** if your module includes models::

    python manage.py makemigrations
    python manage.py migrate

Module Structure
----------------

A well-organized module typically contains::

    platform_django/<module_name>/
    ├── __init__.py
    ├── admin.py              # Django admin configuration
    ├── apps.py               # App configuration
    ├── models.py             # Domain models
    ├── services.py           # Business logic (optional)
    ├── selectors.py          # Read operations (optional)
    ├── managers.py           # Custom model managers (optional)
    ├── migrations/
    │   └── __init__.py
    ├── api/                  # API layer (if using DRF)
    │   ├── __init__.py
    │   ├── serializers.py
    │   └── views.py
    └── tests/
        ├── __init__.py
        ├── factories.py      # Test factories
        └── test_models.py

Best Practices
--------------

**Naming conventions:**

- Use lowercase, singular nouns for module names (e.g., ``billing``, ``notification``, ``inventory``)
- Keep names short but descriptive
- Avoid generic names like ``utils`` or ``helpers``---put shared code in ``core``

**When to create a new module:**

- The domain has its own distinct models and business rules
- The functionality could conceptually be developed by a separate team
- You want to enforce boundaries between areas of the codebase

**When to extend an existing module:**

- The new functionality is tightly coupled to existing models
- It's a minor extension of existing domain logic
- Creating a new module would require excessive cross-module dependencies

**Module communication:**

Modules communicate through explicit interfaces. Two patterns exist:

- **Direct service calls** --- For one-way dependencies where a higher-level module calls a lower-level one. The callee returns a DTO, not an ORM model.
- **Domain events** --- For loose coupling, especially when a lower-level module needs to notify higher-level modules without importing from them.

Key rules:

- Import only from a module's public interface, not internal implementation details
- Dependencies must be acyclic---higher-level modules depend on lower-level ones, never the reverse
- Use events to enable "reverse" communication without creating circular imports

See :doc:`module-dependencies` for the complete decision framework.

Registering Event Handlers
--------------------------

If your module needs to react to events from other modules, register handlers in ``AppConfig.ready()``:

.. code-block:: python

    # platform_django/<module_name>/apps.py
    from django.apps import AppConfig

    class ModuleNameConfig(AppConfig):
        name = "platform_django.<module_name>"
        verbose_name = "Module Name"

        def ready(self) -> None:
            """Register event handlers when the app is ready."""
            from platform_django.domain_events.bus import event_bus
            from platform_django.domain_events.events import SomeEvent
            from platform_django.<module_name>.handlers import handle_some_event

            event_bus.subscribe(SomeEvent, handle_some_event)

Adding API Endpoints
--------------------

To expose your module's functionality via REST API:

#. Create serializers in ``api/serializers.py``
#. Create viewsets in ``api/views.py``
#. Register routes in ``config/api_router.py``

.. code-block:: python

    # config/api_router.py
    from platform_django.<module_name>.api.views import ModuleViewSet

    router.register("<module_name>", ModuleViewSet)

See :doc:`/3-backend-guides/api-development` for API patterns.

See Also
--------

- :doc:`/0-introduction/platform-architecture` --- Platform architecture overview
- :doc:`module-dependencies` --- Valid dependency patterns between modules
- :doc:`module-boundaries` --- Enforcing boundaries with import-linter
- :doc:`event-driven` --- Decoupling modules with domain events
