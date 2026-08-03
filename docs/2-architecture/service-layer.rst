Service Layer Patterns
======================

Business logic organization using services (writes) and selectors (reads), based on the `HackSoft Django Styleguide <https://github.com/HackSoftware/Django-Styleguide>`_.

Progressive Complexity
----------------------

Not every module needs the full service/selector pattern from day one. We follow a **progressive complexity** approach: start simple, and extract structure as your module grows.

Tier 1: Start Simple
^^^^^^^^^^^^^^^^^^^^^

For prototyping, new modules, or simple CRUD endpoints, it is perfectly fine to put business logic directly in your views. This keeps things fast and easy to iterate on:

.. code-block:: python

    # platform_django/tasks/api/views.py
    from rest_framework.views import APIView
    from rest_framework.response import Response
    from rest_framework import serializers, status

    class TaskCreateInputSerializer(serializers.Serializer):
        title = serializers.CharField(max_length=200)
        description = serializers.CharField(required=False, default="")

    class TaskCreateView(APIView):
        def post(self, request):
            serializer = TaskCreateInputSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            # Business logic inline --- fine for simple cases
            task = Task.objects.create(
                title=serializer.validated_data["title"],
                description=serializer.validated_data["description"],
                created_by=request.user,
                status="open",
            )

            return Response({"id": task.id, "title": task.title}, status=status.HTTP_201_CREATED)

There is nothing wrong with this approach for simple modules. It is easy to read, easy to test with API-level tests, and easy to change.

Tier 2: Extract When Needed
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When views start to feel heavy, extract logic into service and selector functions. Signs that it is time:

- A view has more than ~50 lines of business logic
- The same logic is needed in multiple views, a management command, or a Celery task
- Testing the logic requires setting up full HTTP requests
- You need to share read queries with access control across multiple endpoints

At this point, create ``services.py`` and/or ``selectors.py`` in your module and move the logic there:

.. code-block:: python

    # platform_django/tasks/services.py
    def task_create(*, title: str, description: str, created_by: "User") -> Task:
        task = Task(
            title=title,
            description=description,
            created_by=created_by,
            status="open",
        )
        task.full_clean()
        task.save()
        return task

    # platform_django/tasks/api/views.py
    class TaskCreateView(APIView):
        def post(self, request):
            serializer = TaskCreateInputSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            task = task_create(**serializer.validated_data, created_by=request.user)
            return Response(TaskSerializer(task).data, status=status.HTTP_201_CREATED)

Tier 3: Full Pattern
^^^^^^^^^^^^^^^^^^^^^

For production-grade modules with complex business logic, cross-module communication, or strict domain rules, use the complete services/selectors pattern described in the rest of this document. This includes:

- Keyword-only arguments on all service functions
- DTOs for cross-module returns
- Atomic transactions wrapping multi-step mutations
- Selectors with access control
- Separation of public API from internal helpers

When to Adopt
^^^^^^^^^^^^^

Use this decision guide:

.. code-block:: text

    Is this a new module or prototype?
           |
           +---- YES --> Start with Tier 1 (logic in views)
           |
           +---- NO --> Does the module have complex business rules,
                        cross-module calls, or reused logic?
                              |
                              +---- YES --> Use Tier 3 (full pattern)
                              |
                              +---- NO  --> Use Tier 2 (extract key functions)

The key insight is that you can always refactor from Tier 1 to Tier 3 later. Starting simple avoids premature abstraction while still having a clear path forward when complexity demands it.

The Core Principle
------------------

When you are ready for the full pattern, the split is straightforward:

**Services** handle write operations:

- Create, update, or delete data
- Trigger side effects (emails, queued tasks, external APIs)
- Enforce business rules on mutations

**Selectors** handle read operations:

- Query and filter data
- Apply access control to queries
- Return data without side effects

.. code-block:: python

    # platform_django/users/services.py - Write operations
    def user_create(*, email: str, name: str) -> User:
        """Create a new user with profile."""
        user = User(email=email)
        user.full_clean()
        user.save()

        profile_create(user=user, name=name)
        send_welcome_email.delay(user_id=user.id)

        return user

    # platform_django/users/selectors.py - Read operations
    def user_list(*, fetched_by: User) -> QuerySet[User]:
        """Return users visible to the requesting user."""
        if fetched_by.is_staff:
            return User.objects.all()
        return User.objects.filter(is_active=True)

Where Business Logic Should NOT Live
------------------------------------

**Not in views** --- Views handle HTTP only:

.. code-block:: python

    # GOOD - view delegates to service
    class UserCreateView(APIView):
        def post(self, request):
            serializer = UserCreateInputSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = user_create(**serializer.validated_data)
            return Response(UserSerializer(user).data)

**Not in serializers** --- Serializers validate, not mutate:

.. code-block:: python

    # GOOD - serializer only validates
    class UserCreateInputSerializer(serializers.Serializer):
        email = serializers.EmailField()
        name = serializers.CharField(max_length=100)

**Not in signals** --- Signals create hidden coupling. Call the service explicitly.

**Not in model save()** --- Overriding ``save()`` for business logic makes models unpredictable.

Model Properties: The Exception
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Model properties are fine for simple, non-relational computations:

.. code-block:: python

    class User(models.Model):
        first_name = models.CharField(max_length=100)
        last_name = models.CharField(max_length=100)

        @property
        def full_name(self) -> str:
            return f"{self.first_name} {self.last_name}"

Move it to a selector if it queries related objects or has complex business rules.

Writing Services
----------------

Function Signature Pattern
^^^^^^^^^^^^^^^^^^^^^^^^^^

Use keyword-only arguments to force explicit parameter names:

.. code-block:: python

    def user_create(*, email: str, name: str) -> User:
        ...

Return DTOs for Cross-Module Communication
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When services are called from other modules, return data transfer objects:

.. code-block:: python

    from dataclasses import dataclass

    @dataclass(frozen=True)
    class UserDTO:
        id: int
        email: str
        name: str

    def user_get_by_id(user_id: int) -> UserDTO | None:
        """Public interface for other modules."""
        try:
            user = User.objects.get(id=user_id)
            return UserDTO(id=user.id, email=user.email, name=user.name)
        except User.DoesNotExist:
            return None

For internal module use, returning model instances is fine.

.. note::

   DTOs are **required** for cross-module service calls. This keeps internal model
   structures hidden and prevents tight coupling. See :doc:`module-dependencies` for
   which direction a cross-module call may run in.

Atomic Transactions
^^^^^^^^^^^^^^^^^^^

Wrap services that make multiple changes:

.. code-block:: python

    from django.db import transaction

    @transaction.atomic
    def order_create(*, user_id: int, items: list[dict]) -> Order:
        order = Order.objects.create(user_id=user_id, status="pending")
        for item in items:
            OrderItem.objects.create(order=order, **item)
        return order

Writing Selectors
-----------------

Filtering with Access Control
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    def order_list(*, fetched_by: User) -> QuerySet[Order]:
        if fetched_by.is_staff:
            return Order.objects.all()
        return Order.objects.filter(user_id=fetched_by.id)

    def order_get(*, order_id: int, fetched_by: User) -> Order:
        return order_list(fetched_by=fetched_by).get(id=order_id)

Avoid N+1 Queries
^^^^^^^^^^^^^^^^^

.. code-block:: python

    def order_list_with_items(*, fetched_by: User) -> QuerySet[Order]:
        return (
            order_list(fetched_by=fetched_by)
            .prefetch_related("items", "items__product")
            .select_related("shipping_address")
        )

Common Pitfalls
---------------

N+1 queries across modules
^^^^^^^^^^^^^^^^^^^^^^^^^^

Without foreign keys (see :doc:`module-boundaries`), cross-module queries can multiply:

.. code-block:: python

    # BAD - N+1 queries
    def order_list_with_users(fetched_by: User) -> list[dict]:
        orders = order_list(fetched_by=fetched_by)
        return [
            {"order": order, "user": user_get_by_id(order.user_id)}
            for order in orders
        ]

    # BETTER - batch fetch
    def order_list_with_users(fetched_by: User) -> list[dict]:
        orders = list(order_list(fetched_by=fetched_by))
        user_ids = [o.user_id for o in orders]
        users = user_get_by_ids(user_ids)
        users_by_id = {u.id: u for u in users}
        return [
            {"order": order, "user": users_by_id.get(order.user_id)}
            for order in orders
        ]

Public vs Internal Functions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Document which services are part of the module's public API:

.. code-block:: python

    # platform_django/users/services.py

    # === PUBLIC API ===
    def user_create(...): ...
    def user_exists(user_id: int) -> bool: ...

    # === INTERNAL ===
    def _validate_email_domain(email: str) -> bool: ...

Testing
-------

Services and selectors are plain functions, easy to unit test:

.. code-block:: python

    import pytest
    from platform_django.users.services import user_create

    @pytest.mark.django_db
    def test_user_create():
        user = user_create(email="test@example.com", name="Test User")
        assert user.email == "test@example.com"
        assert user.profile.name == "Test User"

See Also
--------

- `HackSoft Django Styleguide <https://github.com/HackSoftware/Django-Styleguide>`_
- :doc:`module-boundaries` --- Enforcing boundaries between modules
- :doc:`module-dependencies` --- Valid dependency patterns between modules
- :doc:`event-driven` --- When a boundary justifies domain events
