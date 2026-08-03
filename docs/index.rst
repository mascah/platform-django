Project Documentation
=====================

Architecture reference for a modular monolith built with Django and Turborepo React.

These docs serve as a reference for understanding the project's architecture and making
informed decisions. They describe patterns and conventions, not mandates. Start simple
and adopt more structure as complexity warrants it.

.. toctree::
   :maxdepth: 2
   :caption: Introduction

   0-introduction/architecture-evolution
   0-introduction/platform-architecture
   0-introduction/ui-architecture

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   1-getting-started/local-setup
   1-getting-started/configuration
   1-getting-started/staying-connected

.. toctree::
   :maxdepth: 2
   :caption: Architecture Patterns

   2-architecture/module-structure
   2-architecture/module-boundaries
   2-architecture/module-dependencies
   2-architecture/service-layer
   2-architecture/event-driven

.. toctree::
   :maxdepth: 2
   :caption: Backend

   3-backend-guides/api-development
   3-backend-guides/authentication
   3-backend-guides/testing
   3-backend-guides/migrations

.. toctree::
   :maxdepth: 2
   :caption: Frontend

   4-frontend-guides/type-safe-api
   4-frontend-guides/component-library

.. toctree::
   :maxdepth: 2
   :caption: Deployment

   7-deployment/tiers

.. toctree::
   :maxdepth: 2
   :caption: Development Workflow

   5-ai-development/claude-code-workflow
   5-ai-development/quality-gates
   6-code-quality/linting-formatting
   6-code-quality/type-checking
   6-code-quality/commit-standards

Indices and tables
==================

* :ref:`genindex`
* :ref:`search`
