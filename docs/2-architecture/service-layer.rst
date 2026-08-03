Service Layer Patterns
======================

Business logic lives in services (writes) and selectors (reads). The `HackSoft
Django Styleguide <https://github.com/HackSoftware/Django-Styleguide>`_ is an
influence on this pattern, not a specification it must satisfy.

.. note::

   ``platform_django/users/`` is the worked example. ``selectors.py`` holds the
   access-scoped read the API viewset serves, ``services.py`` holds the profile
   write both the HTML view and the DRF update mixin call, and
   ``tests/test_services.py`` and ``tests/test_selectors.py`` are the test
   shapes to copy. Read those five files before writing your own.

Progressive Complexity
----------------------

Not every module needs the full split from day one. Start at the first rung
that holds, and climb when the code asks you to --- each rung is reachable from
the one below it by moving code, not by rewriting the module.

Start simple
^^^^^^^^^^^^

For a prototype or a simple CRUD endpoint, business logic in the view is fine:

.. code-block:: python

    class TaskCreateView(APIView):
        def post(self, request):
            serializer = TaskCreateInputSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            # Business logic inline --- fine for simple cases
            task = Task.objects.create(
                **serializer.validated_data,
                created_by=request.user,
                status="open",
            )

            return Response({"id": task.id}, status=status.HTTP_201_CREATED)

Easy to read, easy to test through the API, easy to change.

Extract when needed
^^^^^^^^^^^^^^^^^^^

Move logic into ``services.py`` and ``selectors.py`` when:

- a view carries more than a screenful of business logic;
- the same logic is needed by a second view, a management command or a Celery
  task;
- testing the logic requires setting up an HTTP request to reach it;
- a read query with access control has to be shared across endpoints.

.. code-block:: python

    # platform_django/tasks/services.py
    def task_create(*, title: str, description: str, created_by_id: int) -> Task:
        return Task.objects.create(
            title=title,
            description=description,
            created_by_id=created_by_id,
            status="open",
        )

    # platform_django/tasks/api/views.py
    class TaskCreateView(APIView):
        def post(self, request):
            serializer = TaskCreateInputSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            task = task_create(
                **serializer.validated_data,
                created_by_id=request.user.pk,
            )
            return Response(TaskSerializer(task).data, status=status.HTTP_201_CREATED)

The full pattern
^^^^^^^^^^^^^^^^

A module with real domain rules, cross-module callers or strict invariants uses
everything below: keyword-only signatures, DTOs at the boundary, atomic
transactions around multi-step writes, access-scoped selectors, and a public
interface distinguished from internal helpers.

You can always climb from the first rung to the last. Starting simple avoids
premature abstraction; keeping the write in one place is what makes the climb a
move rather than a rewrite.

The Core Principle
------------------

**Services** handle writes: create, update or delete data, enforce business
rules on mutations, and trigger side effects.

**Selectors** handle reads: query and filter data, apply access control, and
return without writing or causing an externally visible side effect.

.. code-block:: python

    # platform_django/users/services.py --- write operations
    def user_update_profile(*, user_id: int, name: str | None = None) -> User:
        user = User.objects.get(id=user_id)
        if name is not None:
            user.name = name
            user.save(update_fields=["name"])
        return user

    # platform_django/users/selectors.py --- read operations
    def user_list_visible_to(viewer_id: int) -> QuerySet[User]:
        return User.objects.filter(id=viewer_id).order_by("id")

Where Business Logic Should Not Live
------------------------------------

**Not in views** --- views handle HTTP. They call a selector for a read and a
service for a write, and translate the result into a response.

**Not in serializers** --- serializers validate and shape data, they do not
mutate it. A serializer's ``create()`` or ``update()`` that writes puts the
mutation somewhere no other caller can reach.

**Not in signals** --- signals hide the entry point to a workflow and create
implicit coupling. Call the service explicitly. Framework or vendor hooks with
no explicit entry point are the exception.

**Not in model** ``save()`` --- business behaviour in ``save()`` fires on every
write path, including migrations and fixtures.

Model properties: the exception
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A property computing over the model's own local fields is fine:

.. code-block:: python

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

Move it to a selector once it queries related objects or crosses rows.

Writing Services
----------------

Naming and signatures
^^^^^^^^^^^^^^^^^^^^^

Name public operations entity-first, action-second --- ``user_update_profile``,
``order_place`` --- so that everything about one entity sorts and greps
together. Use keyword-only parameters when an operation takes two or more
inputs:

.. code-block:: python

    def user_update_profile(*, user_id: int, name: str | None = None) -> User:
        ...

These are consistency preferences. Neither is worth a review finding on its own
without a concrete readability, compatibility or misuse risk.

Saving
^^^^^^

Save an existing row with ``update_fields``. A bare ``save()`` writes every
column, including ones another request may have changed since this instance was
loaded:

.. code-block:: python

    user.name = name
    user.save(update_fields=["name"])

Call ``full_clean()`` where model validation is deliberately part of that write
path and its errors are useful to the caller. It is not a universal
pre-save requirement.

Transactions and side effects
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Wrap a service that makes several changes in ``transaction.atomic()``. Do not
wrap every single-row write by default:

.. code-block:: python

    @transaction.atomic
    def order_place(*, owner_id: int, items: list[dict]) -> Order:
        order = Order.objects.create(owner_id=owner_id, status="pending")
        for item in items:
            OrderItem.objects.create(order=order, **item)
        return order

Schedule anything that must not happen on a rolled-back write --- an email, a
queued task, an external call --- from ``transaction.on_commit()``, capturing
primitives rather than the ORM instance. See :doc:`module-dependencies`.

Returning across a boundary
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Within the module, returning model instances is fine. A service or selector
called from another module returns primitives or a stable DTO, so that the
caller does not come to depend on the model's field list:

.. code-block:: python

    @dataclass(frozen=True)
    class UserProfileDTO:
        id: int
        email: str
        name: str

Writing Selectors
-----------------

Access control
^^^^^^^^^^^^^^

Scope the base query once, and derive detail lookups from it. That keeps the
not-found and forbidden behaviour identical on both paths instead of growing a
second permission rule later:

.. code-block:: python

    def order_list(*, fetched_by_id: int) -> QuerySet[Order]:
        return Order.objects.filter(owner_id=fetched_by_id).order_by("id")

    def order_get(*, order_id: int, fetched_by_id: int) -> Order:
        return order_list(fetched_by_id=fetched_by_id).get(id=order_id)

Order any queryset a paginator will consume. An unordered queryset behind
``LIMIT``/``OFFSET`` skips and duplicates rows between pages.

Query shape
^^^^^^^^^^^

Add ``select_related`` and ``prefetch_related`` for relations the caller
actually touches, and ``only``/``defer`` to drop expensive columns a list view
never reads. Preload nothing speculatively --- the read path is the evidence.

Batch across boundaries
^^^^^^^^^^^^^^^^^^^^^^^

Where a boundary uses identifiers rather than a relation (see
:doc:`module-boundaries`), a per-row lookup becomes N+1 queries. Fetch once and
join in memory:

.. code-block:: python

    orders = list(order_list(fetched_by_id=viewer_id))
    users_by_id = {u.id: u for u in user_get_many(ids=[o.owner_id for o in orders])}

Public vs internal
^^^^^^^^^^^^^^^^^^

Prefix internal helpers with an underscore. Everything without one is a
contract another caller may depend on.

Testing
-------

Assert behaviour at the HTTP boundary, where it survives logic moving between a
view and a service. Add focused service and selector tests for what that seam
cannot see cheaply --- persistence, the access scope, the exception contract,
and post-commit effects:

.. code-block:: python

    @pytest.mark.django_db
    def test_user_update_profile_persists_the_new_name(user: User):
        user_update_profile(user_id=user.pk, name="Ada Lovelace")

        user.refresh_from_db()
        assert user.name == "Ada Lovelace"

``platform_django/users/tests/`` carries both shapes. See
:doc:`/3-backend-guides/testing`.

See Also
--------

- `HackSoft Django Styleguide <https://github.com/HackSoftware/Django-Styleguide>`_
- :doc:`module-boundaries` --- What the import contracts prove
- :doc:`module-dependencies` --- Which direction a cross-module call may run
- :doc:`event-driven` --- When a boundary justifies domain events
