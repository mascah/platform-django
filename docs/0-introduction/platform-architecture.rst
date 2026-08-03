Platform Architecture
=====================

This documents how we've organized the codebase. It's a starting point---if something doesn't work for your use case, let's discuss.

Project Structure
-----------------

.. code-block:: text

    platform-django/
    ├── apps/                    # Frontend applications (Turborepo workspaces)
    │   ├── platform_django/     # Vite + React SPA (served at /app/)
    │   └── landing/             # Astro static site (marketing/landing pages)
    ├── packages/                # Shared frontend packages
    │   ├── ui/                  # Shared React components (@workspace/ui, shadcn/ui)
    │   ├── eslint-config/       # Shared ESLint config (@workspace/eslint-config)
    │   ├── prettier-config/     # Shared Prettier config (@workspace/prettier-config)
    │   └── typescript-config/   # Shared TypeScript configs (@workspace/typescript-config)
    ├── config/                  # Django settings and configuration
    │   └── settings/            # Environment-specific settings
    ├── libs/                    # Isolated Python packages (no Django dependency)
    ├── platform_django/         # Django application
    │   ├── users/               # User domain module
    │   ├── core/                # Shared utilities and base models
    │   └── [your modules]/      # Add domain modules here
    └── docker/                  # Docker configurations

Backend: Django Modules
-----------------------

We're organizing Django apps in ``platform_django/`` by domain. Each app is intended to be a self-contained module with:

- ``models.py`` --- Domain models
- ``views.py`` or ``api/`` --- HTTP interfaces
- ``services.py`` --- Business logic (available when needed)
- ``selectors.py`` --- Read operations (available when needed)
- ``tests/`` --- Module-specific tests

Add new modules as sibling directories to ``users/``. See :doc:`/2-architecture/module-structure` for steps.

**Patterns we're trying:**

- We're calling downward between modules --- a higher module calls a lower module's service or selector. Events are a decision, not a default. See :doc:`/2-architecture/event-driven`.
- We're enforcing module boundaries with import-linter. See :doc:`/2-architecture/module-boundaries`.
- We're putting business logic in services and read operations in selectors, not views. See :doc:`/2-architecture/service-layer`.

These are starting points. If you hit friction, let's talk about what works better.

Isolated Python Packages (libs/)
--------------------------------

Stateless Python packages that don't depend on Django live in ``libs/``. These are managed as uv workspace members with their own ``pyproject.toml`` and tests.

- **When to use libs/**: Stateless code, no Django dependency, returns Pydantic models (e.g., third-party API clients, data transformations)
- **When to use platform_django/**: Code that needs Django ORM, settings, middleware, or the service/selector pattern

See :doc:`/2-architecture/module-boundaries` for details on the isolation rules enforced by import-linter.

Frontend: Turborepo Monorepo
----------------------------

Frontend applications live in ``apps/`` as Turborepo workspaces. Shared code lives in ``packages/``.

**How things connect:**

1. **Django + Vite**: We use ``django-vite`` to serve React SPAs. Frontend builds go to ``apps/*/dist/`` and Django serves them as static files.

2. **API Client Generation**: We use ``@hey-api/openapi-ts`` to generate typed React Query hooks from Django's OpenAPI schema.

3. **Authentication**: We use ``django-allauth`` with headless mode (``/_allauth/``) for API authentication.

See :doc:`/0-introduction/ui-architecture` for frontend patterns.

Shared Infrastructure
---------------------

Cross-cutting concerns live outside domain modules:

- ``config/settings/`` --- Django configuration
- ``docker/`` --- Container definitions for local development
- ``packages/`` --- Shared frontend code

Where to Start
--------------

- **New to the codebase?** Start with :doc:`/1-getting-started/local-setup`.
- **Adding a feature?** See :doc:`/2-architecture/module-structure` and :doc:`/2-architecture/service-layer`.
- **Working on frontend?** See :doc:`/0-introduction/ui-architecture` and :doc:`/4-frontend-guides/type-safe-api`.
- **Understanding CI/CD?** See :doc:`/6-code-quality/linting-formatting` and :doc:`/5-ai-development/quality-gates`.
