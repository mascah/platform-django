---
name: openapi-client
description: Use when a Django API change affects the generated TypeScript client — serializers, schema annotations, Hey API generation, TanStack Query options, or types under apps/platform_django/src/services/.
---

# OpenAPI Client

The client is generated, not written. Django serializers are the source of
truth; TypeScript types and TanStack Query hooks are derived from them. A
serializer change is a frontend change.

## Inspect first

1. Read the changed serializer, view, URL registration and any `@extend_schema`
   annotation.
2. Read `apps/platform_django/openapi-ts.config.ts`. It is the current generator
   contract; do not paste older snippets from docs into it.
3. Inspect the consuming code before changing imports, query keys or
   invalidation.

## The pipeline

```
Django serializers          drf-spectacular          @hey-api/openapi-ts
platform_django/*/api/  ->  /api/schema/         ->  apps/platform_django/src/services/platform_django/
```

Current generator behaviour:

- output goes to `src/services/platform_django`
- default plugins, plus `@hey-api/client-fetch` and `@tanstack/react-query`
  with `infiniteQueryOptions: false`
- `parser.transforms.readWrite` is **off**, because Django already emits split
  request components — see below

## The read/write split happens server-side

`SPECTACULAR_SETTINGS["COMPONENT_SPLIT_REQUEST"]` is on. Django emits separate
request components — `UserRequest`, `PatchedUserRequest` — that drop read-only
fields and carry write-correct required flags. Without it, read-only fields leak
into write payloads as *required* properties and every mutation has to cast
through `as unknown as`.

Because that split already happened, the generator's own `readWrite` transform
is disabled. Turning it back on splits the split and emits redundant `*Writable`
types alongside the `*Request` ones. Change one of these two settings only
together with the other.

## Regenerate

Django must be running — the generator fetches the live schema.

```bash
cd apps/platform_django && pnpm openapi-ts
```

The configured input is `http://localhost:8000/api/schema`. A worktree runs
Django on its own port, so check `just ports` and point the generator at that
port when it is not 8000; otherwise you regenerate against whatever else is
listening on 8000, or nothing.

Regenerate after adding, changing or removing a serializer field; changing a
view, route or `@extend_schema` annotation; or adding an `@action`.

## Generated files

Never hand-edit anything under `apps/platform_django/src/services/`. It is
excluded from ESLint for that reason. If the output is wrong, fix the
serializer, the schema annotation or the generator config, then regenerate.

Generated TypeScript is a compile-time contract, not proof the runtime response
is correct. Verify serializer fields, read/write behaviour, nullability and
permissions where the change depends on them.

## Verification

- backend test for the changed endpoint or schema —
  `platform_django/users/tests/api/test_openapi.py` is the shape
- `cd apps/platform_django && pnpm openapi-ts`
- `pnpm typecheck` when generated types or their usage changed

## Common misses

- Regenerating against port 8000 from a worktree that serves on another port.
- Editing generated files instead of the serializer behind them.
- Treating generated types as runtime validation.
- Re-enabling `readWrite` while `COMPONENT_SPLIT_REQUEST` is also on.

## References

- `docs/4-frontend-guides/type-safe-api.rst`
- `apps/platform_django/openapi-ts.config.ts`
- `config/settings/base.py` — `SPECTACULAR_SETTINGS`
- `platform_django/users/api/serializers.py` — read-only identity fields, and
  why they are read-only
- the `django-api` skill
