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

```bash
just openapi
```

That dumps the schema with `manage.py spectacular` and runs the generator
against the file, so nothing needs to be serving and there is no port to get
right. Django does not have to be running and neither does the database.

Regenerate after adding, changing or removing a serializer field; changing a
view, route or `@extend_schema` annotation; or adding an `@action`.

To generate against a server that is already up instead, pass its schema URL
with `-i` — a worktree serves on its own port, so `just ports` is where that
port comes from, not 8000. Without `-i` the generator falls back to the URL in
`openapi-ts.config.ts`, which assumes port 8000.

## CI fails on a stale client

The `openapi-client` job regenerates the client and fails on any diff, the same
way `agent-mirrors` guards the skill mirrors. Satisfy it by running
`just openapi` and committing the result.

It exists because staleness is invisible in review: a `.gen.ts` diff that should
be there and is not looks exactly like one that was never needed. This matters
most on a merge with the template. drf-spectacular sorts components
alphabetically, so a project's added types interleave with the template's rather
than colliding, and git merges them cleanly into a file no schema ever produced.

So the rule after any merge that touched serializers, views, schema annotations
or the generator config is to regenerate and commit — never to resolve the
generated files by hand, and never to read a clean auto-merge as evidence the
result is right.

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
- `just openapi`, then confirm the tree is clean — a diff means the client was stale
- `pnpm typecheck` when generated types or their usage changed

## Common misses

- Hand-resolving the generated files in a merge instead of regenerating them.
- Generating with no `-i` from a worktree that serves on a port other than 8000.
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
