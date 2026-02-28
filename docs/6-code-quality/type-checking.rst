Type Checking
=============

The project uses static type checking to catch errors before runtime. Python code is checked with mypy, and TypeScript provides type safety for frontend code.

Python Type Checking (mypy)
---------------------------

Configuration
^^^^^^^^^^^^^

mypy is configured in ``pyproject.toml``:

.. code-block:: toml

    [tool.mypy]
    python_version = "3.13"
    check_untyped_defs = true
    ignore_missing_imports = true
    warn_unused_ignores = true
    warn_redundant_casts = true
    warn_unused_configs = true
    plugins = [
        "mypy_django_plugin.main",
        "mypy_drf_plugin.main",
    ]

    [[tool.mypy.overrides]]
    module = "*.migrations.*"
    ignore_errors = true

    [tool.django-stubs]
    django_settings_module = "config.settings.test"

Running mypy
^^^^^^^^^^^^

Run type checking manually::

    mypy platform_django

mypy also runs automatically in pre-commit hooks.

Writing Type Hints
^^^^^^^^^^^^^^^^^^

Add type hints to function signatures:

.. code-block:: python

    from typing import Optional
    from platform_django.users.models import User


    def get_user_by_email(email: str) -> Optional[User]:
        """Fetch a user by email address."""
        return User.objects.filter(email=email).first()


    def create_user(
        email: str,
        name: str,
        is_active: bool = True,
    ) -> User:
        """Create a new user."""
        return User.objects.create(
            email=email,
            name=name,
            is_active=is_active,
        )

Django Model Typing
^^^^^^^^^^^^^^^^^^^

Use django-stubs for Django-specific types:

.. code-block:: python

    from django.db import models
    from django.db.models import QuerySet


    class Order(models.Model):
        status: models.CharField[str, str]
        total: models.DecimalField

        @classmethod
        def get_pending(cls) -> QuerySet["Order"]:
            return cls.objects.filter(status="pending")

Common Type Patterns
^^^^^^^^^^^^^^^^^^^^

**Optional values**:

.. code-block:: python

    from typing import Optional

    def find_order(order_id: int) -> Optional[Order]:
        return Order.objects.filter(id=order_id).first()

**Collections**:

.. code-block:: python

    from typing import List, Dict

    def get_order_ids(user_id: int) -> List[int]:
        return list(Order.objects.filter(user_id=user_id).values_list("id", flat=True))

    def get_status_counts() -> Dict[str, int]:
        return dict(Order.objects.values("status").annotate(count=models.Count("id")))

**Union types** (Python 3.10+):

.. code-block:: python

    def process_input(value: str | int) -> str:
        return str(value)

TypeScript Type Checking
------------------------

Configuration
^^^^^^^^^^^^^

TypeScript is configured in each app's ``tsconfig.json`` and shared configs in ``packages/typescript-config/``.

Key compiler options:

.. code-block:: json

    {
      "compilerOptions": {
        "strict": true,
        "noImplicitAny": true,
        "strictNullChecks": true,
        "noUnusedLocals": true,
        "noUnusedParameters": true
      }
    }

Running Type Checks
^^^^^^^^^^^^^^^^^^^

Run TypeScript type checking::

    pnpm typecheck

Or via Turbo for all packages::

    pnpm turbo typecheck

API Type Safety
^^^^^^^^^^^^^^^

Types are auto-generated from the Django OpenAPI schema:

.. code-block:: bash

    cd apps/platform_django
    pnpm openapi-ts

This creates types in ``src/services/platform_django/types.gen.ts``:

.. code-block:: typescript

    // Auto-generated types
    export type User = {
      readonly id: number;
      email: string;
      name: string;
      readonly created_at: string;
    };

    export type Order = {
      readonly id: number;
      status: 'pending' | 'processing' | 'completed';
      total: string;  // Decimal as string
    };

Use these types in your components:

.. code-block:: tsx

    import type { User, Order } from '@/services/platform_django/types.gen';

    function UserCard({ user }: { user: User }) {
      return <div>{user.name}</div>;
    }

See :doc:`/4-frontend-guides/type-safe-api` for complete API integration patterns.

Pre-commit Integration
----------------------

Type checking runs automatically on commit via Lefthook:

.. code-block:: yaml

    # lefthook.yml
    pre-commit:
      commands:
        mypy:
          glob: '*.py'
          exclude: '^docs/|/migrations/'
          run: uv run mypy . --config-file=pyproject.toml

        turbo-typecheck:
          glob: '*.{ts,tsx}'
          exclude: 'node_modules|dist|\.next'
          run: pnpm turbo typecheck

Ignoring Type Errors
--------------------

Sometimes you need to ignore type errors. Use sparingly:

**Python (mypy)**:

.. code-block:: python

    # Ignore a specific line
    result = some_untyped_function()  # type: ignore[no-untyped-call]

    # Ignore with reason (preferred)
    result = legacy_code()  # type: ignore[arg-type]  # TODO: Fix in #123

**TypeScript**:

.. code-block:: typescript

    // @ts-ignore - Legacy code, tracked in #456
    const result = untypedFunction();

    // Better: @ts-expect-error with explanation
    // @ts-expect-error - Third-party types are incomplete
    const data = externalLib.getData();

Best Practices
--------------

1. **Start strict**: Enable strict mode from the beginning
2. **Type public APIs**: Always type function parameters and return values
3. **Avoid ``any``**: Use ``unknown`` and narrow types instead
4. **Document exceptions**: Add comments explaining type ignores
5. **Keep types updated**: Regenerate API types after backend changes

See Also
--------

- :doc:`linting-formatting` --- Code style and linting
- :doc:`/4-frontend-guides/type-safe-api` --- API type generation
- `mypy Documentation <https://mypy.readthedocs.io/>`_
- `TypeScript Handbook <https://www.typescriptlang.org/docs/handbook/>`_
