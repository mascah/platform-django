API Development
===============

We use Django REST Framework for the API layer.

Overview
--------

The API layer sits between HTTP requests and the service layer (see :doc:`/2-architecture/service-layer`). DRF handles:

- Request/response validation via serializers
- Authentication and permissions
- OpenAPI documentation via drf-spectacular

For frontend type safety, see :doc:`/4-frontend-guides/type-safe-api`.

Basic Pattern
-------------

With the services pattern, views are thin orchestration layers:

.. code-block:: python

    # platform_django/tasks/api/serializers.py
    from rest_framework import serializers

    class TaskCreateInputSerializer(serializers.Serializer):
        title = serializers.CharField(max_length=200)
        description = serializers.CharField(required=False)

    class TaskSerializer(serializers.Serializer):
        id = serializers.IntegerField(read_only=True)
        title = serializers.CharField()
        description = serializers.CharField()
        status = serializers.CharField()
        created_at = serializers.DateTimeField()


    # platform_django/tasks/api/views.py
    from rest_framework import status
    from rest_framework.response import Response
    from rest_framework.views import APIView

    from platform_django.tasks.services import task_create
    from platform_django.tasks.selectors import task_list
    from .serializers import TaskCreateInputSerializer, TaskSerializer

    class TaskListCreateView(APIView):
        def get(self, request):
            tasks = task_list(fetched_by=request.user)
            return Response(TaskSerializer(tasks, many=True).data)

        def post(self, request):
            serializer = TaskCreateInputSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            task = task_create(
                created_by=request.user,
                **serializer.validated_data,
            )

            return Response(TaskSerializer(task).data, status=status.HTTP_201_CREATED)

Key points:

- **Input serializers** validate request data
- **Output serializers** format response data
- **Views** call services/selectors, don't contain business logic

Routing
-------

Register views in ``config/api_router.py``:

.. code-block:: python

    from django.urls import path
    from platform_django.tasks.api.views import TaskListCreateView

    urlpatterns = [
        path("tasks/", TaskListCreateView.as_view(), name="task-list-create"),
    ]

OpenAPI Documentation
---------------------

drf-spectacular generates OpenAPI schemas automatically. Access at:

- ``/api/schema/`` — JSON schema
- ``/api/docs/`` — Swagger UI

See Also
--------

- :doc:`/4-frontend-guides/type-safe-api` — End-to-end type safety with React
- :doc:`/2-architecture/service-layer` — Where business logic belongs
- `Django REST Framework <https://www.django-rest-framework.org/>`_ — Official docs
