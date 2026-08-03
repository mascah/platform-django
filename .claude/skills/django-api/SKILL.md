---
name: django-api
description: Use when adding, changing, or reviewing Django REST Framework endpoints, serializers, viewsets, actions, URL routes, or OpenAPI annotations under platform_django/.
---

# Django API

Start by reading the current module code and nearby tests before editing
anything. Prefer current behavior over older prose when they differ.

## Preflight

Inspect the target module's:

- API entrypoints (`api/views.py`, `api/serializers.py`, `config/api_router.py`)
- selector and service call sites
- nearby API tests

`platform_django/users/api/` is the worked example: `GenericViewSet` with three
mixins, `get_queryset` delegating to a selector, and `perform_update`
delegating to a service.

Decide the shape from the code already there:

- `APIView` for a small endpoint
- `ViewSet` for routing shells or custom actions without a queryset
- `GenericViewSet` plus only the mixins you need when DRF behavior helps
- `ModelViewSet` when the module already uses it and the write handlers still
  delegate to a service

Do not default to `ModelSerializer` or `get_queryset()` just because DRF offers
them. Model-backed serializers and viewsets are valid when serializers stay at
the HTTP boundary and writes still go through services.

## Implementation

Keep views thin:

- reads call selectors
- writes call services
- serializers validate and shape HTTP data only
- map domain errors to HTTP responses in the view

A viewset that builds its queryset from a selector has no class-level
`queryset` for the router to infer route names from, so register it with an
explicit `basename`.

Choose the write surface rather than inheriting it. A `ModelSerializer` makes
every listed field writable by default, which is how an endpoint acquires the
power to change fields it does not own — in `users`, `email` and `username` are
allauth's, and both are `read_only` for that reason. State which fields are
writable and why the rest are not.

If a view splats `validated_data` into a service, the serializer's writable
fields and the service's parameters must agree. With a `ModelSerializer` that
field list answers to the model, not to the signature, so pin the coupling with
a test — see `platform_django/users/tests/api/test_serializers.py`. Separate
input and output serializers are the other way to make that safe, and the right
move once the write path outgrows a `ModelSerializer`.

For output on an endpoint that is not model-backed, use `serializers.Serializer`
over DTOs or dicts. For list endpoints, spell out the response schema rather
than relying on queryset inference:

```python
@extend_schema(responses={200: OrderSerializer(many=True)})
def get(self, request):
    return Response(OrderSerializer(order_list(fetched_by_id=request.user.pk), many=True).data)
```

Follow the module's current routing style. If it already uses nested routers or
path parameters, extend that shape instead of flattening it.

## After an API change

The TypeScript client is generated from the schema, so a serializer change is a
frontend change. See the `openapi-client` skill.

## Tests

Add or update focused API tests near the module:

- happy-path status code and body shape
- auth and permission gates
- validation failures
- selector/service error mapping (`404`, `400`)
- fields that must *not* be writable, asserted by attempting the write

Drive the endpoint through DRF's `APIClient` rather than constructing the
viewset, so the test survives logic moving between the view and a service.

## Verification

- targeted `pytest` for the API tests you changed
- `uv run lint-imports` — the API viewset may not import the model directly
- `git diff --check`

## Caution

Treat domain events as candidate architecture, not default API work. Do not
invent event flows; the template ships no event bus.

## References

- `docs/3-backend-guides/api-development.rst`
- `docs/2-architecture/service-layer.rst` — what the view delegates to
- `docs/4-frontend-guides/type-safe-api.rst` — the generated client pipeline
- `platform_django/users/api/` and `platform_django/users/tests/api/`
- `config/api_router.py`
