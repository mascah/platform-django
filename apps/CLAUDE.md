# Frontend Applications

## Structure

- Each app is a Vite + React SPA (or Astro site)
- `apps/platform_django/` — Main app (served via django-vite)
- `apps/landing/` — Landing page (Astro)

## API Client Generation

After backend API changes:

```bash
cd apps/platform_django && pnpm openapi-ts
```

Generates typed hooks in `src/services/platform_django/`

## Type-Safe API Usage

- Query: `useQuery(getUserOptions({ path: { id } }))`
- Mutation: `useMutation(createUserMutation())`
- Invalidate queries on mutation success

## Feature Structure

```
src/features/<feature>/
├── components/    # Feature-specific components
├── contexts/      # React contexts
├── pages/         # Route pages
└── index.ts       # Public exports
```

## Testing

- Playwright for E2E tests
- Page Object Model pattern
- Use `data-testid` for selectors
- Session storage reuse for auth
