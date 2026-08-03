---
name: vite-django
description: Use when changing how a Vite application is mounted or served by Django — templates, django-vite tags, manifests, CSP nonces, static assets, or dev-server behavior.
---

# Vite Django

Django serves the HTML shell; Vite serves the JavaScript. In development Vite
runs a dev server with HMR; in production Vite builds hashed bundles that Django
serves through WhiteNoise. Live config is the authority — do not scaffold a new
app when the request is only to add a route or a template to the existing one.

## Inspect first

1. `config/urls.py` — the mount and the SPA catch-all.
2. `platform_django/templates/apps/platform_django.html` — the shell.
3. `config/settings/base.py` (`DJANGO_VITE`, `STATICFILES_DIRS`) and
   `config/settings/local.py` (dev CSP allowlists).
4. `apps/platform_django/vite.config.ts`.
5. `platform_django/core/templatetags/vite_csp.py`.

## The existing mount

`/app/` and `/app/<path:path>` both render the same template through
`login_required(TemplateView...)`, and the React router handles everything
below. Adding a screen to the React app needs no Django change at all — the
catch-all already serves it.

Add a Django URL, view or template only when the catch-all genuinely cannot
serve the requirement. Keep the existing auth, context processors and template
runtime configuration unless the task explicitly changes them.

The template shell carries, in order: `{% csrf_token %}` for mutating API
requests, `{% vite_hmr_client %}`, `{% vite_react_refresh_csp %}` and
`{% vite_asset 'main.tsx' %}`, then the `#root` mount point. Use the
CSP-aware refresh tag, not a bare `vite_react_refresh` — `vite_csp.py` exists
because django-vite does not resolve the nonce from template variables, and
dropping the nonce breaks React Refresh under the local policy.

The landing page is not this app. `apps/landing` is Astro, pre-rendered and
served by `serve_landing_page` in `config/urls.py`, which injects the CSP nonce
into its script tags itself.

## Development and production

In development, `DJANGO_VITE_DEV_MODE` (defaulting to `DEBUG`) makes the tags
point at the Vite dev server, and `local.py` derives the CSP allowlists from
`DJANGO_VITE` — including the `ws://` origins HMR needs. In a worktree the port
comes from `VITE_PORT`; check `just ports`.

In production, `pnpm build` writes hashed assets and a `manifest.json` under
`apps/platform_django/dist/platform_django/`, `collectstatic` copies them, and
WhiteNoise serves them. `STATICFILES_DIRS` includes the `dist` directory, and
`DJANGO_VITE`'s `manifest_path` points at the manifest. Both must move together
if the build output location changes.

Do not hardcode topology. Ports, static prefixes, manifest paths and dev/prod
behaviour all come from current config.

## A genuinely separate Vite app

Create one only when it needs a separate runtime or deployment surface. Then add
the minimum matching entries: a `DJANGO_VITE` entry, its `dist` directory in
`STATICFILES_DIRS`, a template, a URL and catch-all, and a workspace entry if
`apps/*` does not already cover it. The dev CSP allowlists are derived from
`DJANGO_VITE`, so they need no separate edit.

## Verification

- template, view or URL change: focused Django test for auth, context or the
  rendered tags
- config or static change: the narrow Django or build check that exercises it
- frontend change: `cd apps/platform_django && pnpm build` or `pnpm typecheck`

## Common misses

- Treating a new client route as a new Vite app.
- Dropping the CSP nonce or the CSRF token from the shell.
- Moving the build output without updating both `STATICFILES_DIRS` and
  `manifest_path`.
- Assuming port 5173 in a worktree.

## References

- `docs/0-introduction/ui-architecture.rst`
- `config/urls.py`, `config/settings/base.py`, `config/settings/local.py`
- `platform_django/templates/apps/platform_django.html`
- `platform_django/core/templatetags/vite_csp.py`
- `apps/platform_django/vite.config.ts`
- `Procfile` and `app.json` — how the frontend is built on a deploy
