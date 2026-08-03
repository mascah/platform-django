# Shared Packages (Turborepo)

Everything here is consumed by more than one workspace member. Inspect the
actual consumers before changing a component or a config — `pnpm lint` and
`pnpm typecheck` run across all of them.

## Structure

- `packages/ui/` — Shared UI components and theme
- `packages/eslint-config/` — ESLint configurations
- `packages/prettier-config/` — Prettier configurations
- `packages/typescript-config/` — TypeScript configurations

## UI Package (@workspace/ui)

- Import: `@workspace/ui/components/<name>`, `@workspace/ui/lib/utils`, `@workspace/ui/hooks/<name>`
- Uses shadcn/ui components (Radix primitives + Tailwind CSS)
- Dark mode support via `next-themes`
- Icons via `lucide-react`
- Global styles: `@workspace/ui/globals.css`

## Using Shared Configs

```json
// package.json
{
  "devDependencies": {
    "@workspace/eslint-config": "workspace:*",
    "@workspace/prettier-config": "workspace:*",
    "@workspace/typescript-config": "workspace:*"
  }
}
```
