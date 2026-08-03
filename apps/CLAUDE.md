# Frontend Applications

- `apps/platform_django/` — the React SPA, built by Vite and served by Django at
  `/app/`. Use the `vite-django` skill for anything about how it is mounted.
- `apps/landing/` — the Astro landing page, pre-rendered and served at `/`.

Both are workspace members; shared UI and configs live in `packages/`.

## The API client is generated

`src/services/platform_django/` is generated from Django's OpenAPI schema and is
never hand-edited. If the output is wrong, fix the serializer or the schema
annotation and regenerate. Use the `openapi-client` skill — it covers the
read/write split and the fact that the generator's configured port is not this
worktree's port.

Generated names follow the operation IDs, so hooks read as `usersListOptions()`,
`usersRetrieveOptions({ path: { username } })` and
`usersPartialUpdateMutation()`. Invalidate with the matching `...QueryKey()` on
mutation success.

## Feature structure

```
src/features/<feature>/
├── components/
├── contexts/
├── pages/
└── index.ts       # public exports — import a feature through this
```

## Tests

No unit-test runner is wired here: `pnpm test` runs a Turbo task no package
implements yet. Cover user-visible behaviour with the Playwright suite in `e2e/`
— page objects, `data-testid` selectors, stored auth state. Read the `add-tests`
skill before wiring a runner of your own.
