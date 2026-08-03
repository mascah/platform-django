Why a Modular Monolith?
=======================

The Short Version
-----------------

Distributed architectures solve real problems---independent deployments, team autonomy, isolated failures. But they also come with operational overhead: service discovery, network debugging, distributed tracing, data consistency across services. Sometimes that overhead is worth it. Sometimes it isn't.

This project uses a modular monolith because it gives us most of the benefits (clear boundaries, independent modules, testability) without some of the operational complexity. One deployment. One database. Shared authentication. Simpler local development.

This isn't a judgment call on distributed services. It's a different tradeoff for a different context.

When This Approach Works Well
-----------------------------

A modular monolith tends to fit when:

- Teams share a database or need transactional consistency across domains
- Local development benefits from everything running in one process
- Operational simplicity matters more than independent deployments
- You want clear module boundaries but don't need service-level isolation

When It Doesn't
---------------

Distributed services make more sense when:

- Teams need fully independent deployment schedules
- Workloads have dramatically different scaling characteristics
- Failure isolation between components is critical
- You're integrating systems written in different languages or owned by different organizations

Most real systems end up with some of both. That's expected.

How Modules Keep Things Separate
--------------------------------

Even in a single codebase, we maintain boundaries:

- Each domain gets its own Django app in ``platform_django/``
- Modules communicate through explicit interfaces---a higher module calls a lower module's service or selector
- We use import-linter to catch accidental cross-module dependencies
- Testing can happen at the module level

See :doc:`/2-architecture/module-structure` and :doc:`/2-architecture/module-boundaries` for details.
