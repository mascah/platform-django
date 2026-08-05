# Server-rendered pages take their CSS from the frontend build

The stylesheet for every page Django renders from a template is a CSS-only entry
in the application's Vite build. `apps/platform_django/src/django.css` imports
`@workspace/ui/globals.css` — the same design tokens the landing page and the
application already read — and declares `@source` over
`platform_django/templates`, so Tailwind sees the classes those templates use.
`base.html` references the built file with `{% vite_asset_url %}`. Bootstrap,
its CDN and `django-crispy-forms` are removed, and the authentication pages,
the user pages and the error pages land on the tokens the rest of the product
uses.

## Considered Options

**`django-tailwind-cli` was rejected**, and its appeal was real: a page styled
by `just serve` alone, with no frontend process running, and a watcher wired
into `runserver`. Three things weigh against it here. It downloads the
standalone Tailwind binary from GitHub releases, which is the fetch pattern
`mise.toml` already declines for the whole toolchain — unauthenticated, rate
limited at 60 per hour per IP, and routinely exhausted by other tenants on the
shared egress of a cloud agent VM, a NAT'd CI runner or a Heroku build. It pins
`TAILWIND_CLI_VERSION` independently of the `tailwindcss` version pnpm resolves,
so the product would have two Tailwind versions to keep honest. And the tokens
live in `packages/ui` inside the pnpm workspace, which `globals.css` reaches
through a `tw-animate-css` import out of `node_modules` — so the Node-free build
is not actually Node-free, and the alternative is a second copy of the tokens
that drifts from the first.

**A dedicated workspace package for the Django stylesheet was rejected** as a
`package.json`, a `tsconfig.json` and a turbo target for one CSS file. The
application's build already emits into a `STATICFILES_DIRS` entry and already
writes a manifest `django-vite` reads.

**`{% vite_asset %}` was rejected** on reading `django_vite`'s source rather
than its README. For a CSS entry it emits `<script type="module">` pointing at
the `.css` file in production, which the browser refuses on MIME type, while
behaving correctly in `DEBUG` — a failure that is invisible in every environment
where anyone looks at the pages. `{% vite_asset_url %}` inside a `<link>` is
used instead. That is also why `local.py` adds the Vite dev servers to
`style-src` and not only to `script-src` and `connect-src`.

**`crispy-forms` was removed rather than repacked.** It was not decoration: the
three-line `allauth/elements/fields.html` override piped every authentication
form through `crispy-bootstrap5`, so the 69-line `field.html` override was
reached only where allauth calls `{% element field %}` directly. Swapping the
pack for `crispy-tailwind` would introduce a third styling vocabulary — Tailwind
v2/v3 class names that know nothing of the tokens — to avoid rewriting one
three-line file.

## Consequences

**A server-rendered page is unstyled until the frontend has built.** `just
serve` on its own is no longer enough to see one, which is precisely what
`django-tailwind-cli` would have bought. What is gained in exchange is a live
loop: Tailwind's `@source` watches the Django templates, so a class typed into a
template appears without rebuilding anything.

**The production wiring is the only part with no visual signal**, so it carries
the one test: rendering the sign-in page with `dev_mode` off must emit the
manifest's hashed stylesheet and no `cdnjs`. Manual checking in `DEBUG` takes
the other branch and can never catch it.

**Components are semantic classes in `django.css`, not copied utility strings.**
Both sides read the same CSS variables, so colour and radius stay in sync
automatically and only geometry and typography can drift. The alternative does
not survive the repository anyway: `djlint --reformat` runs on staged templates
at 119 columns, and the shadcn button's base class string is 340 characters
before variants.

**Removing Bootstrap removes `cdnjs.cloudflare.com`** from `script-src`,
`style-src` and `connect-src` in both `base.py` and `local.py`, and removes the
last JavaScript from the server-rendered pages — so the navigation carries no
collapsible menu.

**Server-rendered pages are light only**, matching the landing page, which sets
no theme either. The application follows the operating system through
`ThemeProvider`, so a dark-preferring visitor still meets the theme change on
entering the application. This decision does not widen that seam, and closing it
means giving the landing page a theme first.

**`field.html` becomes the single definition of a form field.** allauth's
`login.html` passes `unlabeled=True` to the fields element, and the label
survives today only because crispy ignores it; the replacement must keep an
accessible label, or `e2e/auth/auth.setup.ts` fails to sign in and takes the
whole browser suite with it.
