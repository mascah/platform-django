UI Architecture Philosophy
==========================

We're taking a pragmatic, multi-tier approach to building user interfaces. Rather than forcing a single frontend paradigm, we have a choice of tools: from simple Django templates to fully interactive React applications.

The Core Principle
------------------

Not every page needs React. Not every page can get by with server-rendered HTML. The key is matching your UI approach to the actual requirements:

- **Prototyping and simple pages**: Django templates
- **Highly interactive applications**: Vite-based SPAs (React) integrated via django-vite
- **Marketing and content pages**: Astro static site (``apps/landing/``) or pre-rendered assets served through Django

Each approach is immediately available. You choose based on your needs, not your tooling constraints.

Tier 1: Django Templates (Simple)
---------------------------------

For admin dashboards, forms, settings pages, and rapid prototyping, Django templates remain the simplest and most productive choice. Standard Django template features (template tags, filters, template inheritance) cover most server-rendered needs.

**Best for**: Admin interfaces, settings pages, forms, server-rendered content, rapid prototyping.

Tier 2: Vite-Based SPAs (Interactive)
-------------------------------------

When you need rich client-side interactivity (complex state management, real-time updates, data visualizations), reach for React.

django-vite Integration
^^^^^^^^^^^^^^^^^^^^^^^

The project uses `django-vite`_ to bridge Django and Vite-based frontends:

- **Hot Module Replacement** in development
- **Manifest-based asset versioning** in production
- **Django template integration**

The Django template bootstraps your SPA:

.. code-block:: html+django

    {% load django_vite %}

    <!DOCTYPE html>
    <html lang="en">
      <head>
        {% vite_hmr_client app='platform_django' %}
        {% vite_react_refresh app='platform_django' %}
        {% vite_asset 'main.tsx' app='platform_django' %}
      </head>
      <body>
        <div id="root"></div>
      </body>
    </html>

The ``vite_hmr_client`` and ``vite_react_refresh`` tags enable hot reloading during development. In production, ``vite_asset`` reads from Vite's manifest to include cache-busted asset URLs.

Vite Configuration
^^^^^^^^^^^^^^^^^^

The key Vite settings for Django integration:

.. code-block:: typescript

    // vite.config.ts
    export default defineConfig({
      base: '/static/platform_django',  // Matches Django's static URL
      build: {
        manifest: 'manifest.json',  // Required for django-vite
        outDir: path.join('dist', 'platform_django'),
      },
    });

Django Settings
^^^^^^^^^^^^^^^

Configure the django-vite app in settings:

.. code-block:: python

    # settings/base.py
    DJANGO_VITE = {
        "platform_django": {
            "dev_mode": DEBUG,
            "dev_server_port": 5173,
            "static_url_prefix": "platform_django",
            "manifest_path": BASE_DIR / "apps/platform_django/dist/platform_django/manifest.json",
        },
    }

    STATICFILES_DIRS = [
        BASE_DIR / "apps/platform_django/dist",  # Include built assets
    ]

**Best for**: Complex dashboards, real-time applications, data-heavy UIs.

Tier 3: Astro Static Site (Landing Pages)
-----------------------------------------

For marketing pages, landing pages, and content-heavy sites that benefit from static generation, ``apps/landing/`` provides an Astro-based static site. Astro generates lightweight HTML with minimal JavaScript, making it ideal for fast-loading public pages.

**Best for**: Marketing sites, landing pages, documentation, SEO-critical content.

Choosing the Right Approach
---------------------------

+---------------------------+----------------------+----------------------+----------------------+
| Requirement               | Django Templates     | Vite SPA             | Astro Static Site    |
+===========================+======================+======================+======================+
| Server-rendered HTML      | Yes                  | No                   | Yes (pre-rendered)   |
+---------------------------+----------------------+----------------------+----------------------+
| SEO-friendly              | Yes                  | Requires SSR         | Yes                  |
+---------------------------+----------------------+----------------------+----------------------+
| Complex client state      | No                   | Yes                  | Limited              |
+---------------------------+----------------------+----------------------+----------------------+
| Build step required       | No                   | Yes                  | Yes                  |
+---------------------------+----------------------+----------------------+----------------------+
| Hot module replacement    | No                   | Yes                  | Yes                  |
+---------------------------+----------------------+----------------------+----------------------+
| TypeScript support        | No                   | Yes                  | Yes                  |
+---------------------------+----------------------+----------------------+----------------------+
| Best for                  | Admin, forms,        | Dashboards, apps,    | Landing pages,       |
|                           | prototypes           | complex UIs          | marketing, content   |
+---------------------------+----------------------+----------------------+----------------------+

The Monorepo Advantage
----------------------

With Turborepo, all frontend approaches share:

- **Common component library** in ``packages/ui/`` (shadcn/ui with Tailwind CSS)
- **Shared TypeScript, ESLint, and Prettier configs**
- **Single** ``pnpm build`` **command** builds everything
- **Unified dependency management** via pnpm workspaces

This means your application interfaces can all use the same design system without duplication.

Further Reading
---------------

- `django-vite`_ --- Vite integration for Django
- `shadcn/ui`_ --- Beautifully designed components built with Radix UI and Tailwind CSS
- `Radix Primitives`_ --- Unstyled, accessible UI primitives for React
- `Tailwind CSS`_ --- Utility-first CSS framework

.. _django-vite: https://github.com/MrBin99/django-vite
.. _shadcn/ui: https://ui.shadcn.com/
.. _Radix Primitives: https://www.radix-ui.com/primitives
.. _Tailwind CSS: https://tailwindcss.com/
