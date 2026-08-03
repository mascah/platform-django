Configuration Reference
=======================

This guide documents environment variables and Django settings.
Configuration follows `Twelve-Factor App <https://12factor.net/config>`_ principles,
using `django-environ <https://django-environ.readthedocs.io/>`_ for typed environment parsing.

.. note::

   **Understanding "Required" values**: In the tables below, "Yes" means required in all environments.
   "Prod" means required only in production --- these are typically cloud service credentials that
   aren't needed for local development, where we use Docker containers or mock services instead.

Environment Variables
---------------------

Core Django Settings
^^^^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 30 15 55

   * - Variable
     - Required
     - Description
   * - ``DJANGO_SECRET_KEY``
     - Yes
     - Secret key for cryptographic signing. Generate with ``python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"``
   * - ``DJANGO_DEBUG``
     - No
     - Enable debug mode. Default: ``False``. Never enable in production.
   * - ``DJANGO_ALLOWED_HOSTS``
     - Yes (prod)
     - Comma-separated list of allowed hostnames.
   * - ``DJANGO_SETTINGS_MODULE``
     - No
     - Settings module to use. Default: ``config.settings.local``

Database
^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 30 15 55

   * - Variable
     - Required
     - Description
   * - ``DATABASE_URL``
     - No
     - PostgreSQL connection string. Format: ``postgres://user:pass@host:port/dbname``.
       When set it is used unchanged; otherwise it is composed from the primitives below
       by ``config/env.py``.
   * - ``POSTGRES_DB`` / ``POSTGRES_USER`` / ``POSTGRES_PASSWORD``
     - Yes (unless ``DATABASE_URL`` is set)
     - Primitives the connection string is composed from.
   * - ``POSTGRES_HOST`` / ``POSTGRES_PORT``
     - No
     - Default: ``localhost`` and ``5432``. Containers override these with service names.

Redis and Caching
^^^^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 30 15 55

   * - Variable
     - Required
     - Description
   * - ``REDIS_URL``
     - No
     - Redis connection string. Format: ``redis://host:port/db``. When set it is used
       unchanged; otherwise it is composed from the primitives below.
   * - ``REDIS_HOST`` / ``REDIS_PORT`` / ``REDIS_DB``
     - No
     - Default: ``localhost``, ``6379`` and ``0``.
   * - ``CELERY_BROKER_URL``
     - No
     - Celery broker URL. Defaults to ``REDIS_URL`` if not set.

Worktree Isolation
^^^^^^^^^^^^^^^^^^

One Postgres and one Redis serve every worktree on the machine, so a worktree does
not run a stack of its own. ``bin/env-refresh`` computes these on first write and
records them in ``.env``; an existing value is never moved, so re-running is safe.

.. list-table::
   :header-rows: 1
   :widths: 30 15 55

   * - Variable
     - Required
     - Description
   * - ``PROJECT_SLUG``
     - No
     - Names this project's database, cache key prefix and Celery queue. Defaults to the checkout's directory name, so a second copy of the template does not land on the first's database. The backing services are shared across projects, not just worktrees.
   * - ``PROJECT_DISPLAY_NAME``
     - No
     - What a user reads: page titles, the navigation brand, the landing page, the API schema title, the from-address on an email. Defaults to ``PROJECT_SLUG`` made readable. Quote the value --- it is the one variable here that usually contains a space.
   * - ``POSTGRES_DB``
     - No
     - ``{PROJECT_SLUG}_{worktree}`` in a worktree, ``{PROJECT_SLUG}`` in the main checkout.
   * - ``REDIS_DB``
     - No
     - The worktree's Redis logical index, so cached and queued values do not leak between branches. One Redis serves 16.
   * - ``DJANGO_PORT``
     - No
     - Port for the Django process. Default: ``8000``. Each worktree gets a free one.
   * - ``VITE_PORT``
     - No
     - Port for the platform_django Vite dev server. Default: ``5173``. Each worktree gets a free one.

Django and Vite are application processes running on the host, so these two are the
only ports that need allocating. Sibling worktrees are read out of their own ``.env``
files to find a free value, so there is no registry to go stale.

Email
^^^^^

.. list-table::
   :header-rows: 1
   :widths: 30 15 55

   * - Variable
     - Required
     - Description
   * - ``DJANGO_DEFAULT_FROM_EMAIL``
     - No
     - Default sender email address.
   * - ``DJANGO_EMAIL_BACKEND``
     - No
     - Email backend class. Default: console backend in development.

Settings Files
--------------

Django settings are organized by environment in ``config/settings/``:

- ``base.py`` --- Shared settings for all environments
- ``local.py`` --- Development settings (imports from base)
- ``test.py`` --- Test runner settings
- ``production.py`` --- Production settings with security hardening

Local Development
^^^^^^^^^^^^^^^^^

Local development uses ``config.settings.local`` by default. Key differences from production:

- ``DEBUG = True``
- Console email backend
- Relaxed security settings
- Verbose logging

Production
^^^^^^^^^^

Production uses ``config.settings.production``. Key settings:

- ``DEBUG = False``
- HTTPS enforcement (``SECURE_SSL_REDIRECT``)
- Secure cookies (``SESSION_COOKIE_SECURE``, ``CSRF_COOKIE_SECURE``)
- HSTS headers

Every value a deployment needs to differ on is read from the environment, so a
project changes it by setting a variable rather than by editing a tracked file.
The variables are declared in ``app.json``; these two are the ones a project
most often wants:

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Variable
     - Purpose
   * - ``DJANGO_SECURE_HSTS_SECONDS``
     - How long browsers are told to require HTTPS. Defaults to ``60``. A
       browser honours this for the whole window, so a long value set before
       HTTPS is proven locks visitors out of a host that cannot yet serve them.
       Raise it to ``518400`` once the short window has held.
   * - ``DJANGO_API_SERVER_URL``
     - Public base URL advertised in the OpenAPI schema's ``SERVERS`` block,
       used by tools that generate API code samples. Defaults to
       ``https://example.com``.

Django REST Framework
---------------------

API settings in ``config/settings/base.py``:

.. code-block:: python

    REST_FRAMEWORK = {
        "DEFAULT_AUTHENTICATION_CLASSES": (
            "rest_framework.authentication.SessionAuthentication",
            "rest_framework.authentication.TokenAuthentication",
        ),
        "DEFAULT_PERMISSION_CLASSES": (
            "rest_framework.permissions.IsAuthenticated",
        ),
        "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
        "DEFAULT_PAGINATION_CLASS": "platform_django.core.pagination.DefaultPagination",
    }

OpenAPI Schema
^^^^^^^^^^^^^^

drf-spectacular settings for API documentation:

.. code-block:: python

    SPECTACULAR_SETTINGS = {
        "TITLE": "Platform Django API",
        "DESCRIPTION": "Documentation of API endpoints",
        "VERSION": "1.0.0",
        "SERVE_PERMISSIONS": ["rest_framework.permissions.IsAdminUser"],
        "SCHEMA_PATH_PREFIX": "/api/",
    }

The schema is served at ``/api/schema/`` and Swagger UI at ``/api/docs/``.

Celery Configuration
--------------------

Celery settings for background tasks:

.. code-block:: python

    CELERY_BROKER_URL = env("CELERY_BROKER_URL", default=env("REDIS_URL"))
    CELERY_RESULT_BACKEND = CELERY_BROKER_URL
    CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=False)

Set ``CELERY_TASK_ALWAYS_EAGER=True`` in tests to run tasks synchronously.

Adding New Settings
-------------------

When adding new configuration:

1. **Add to base.py** with a sensible default or ``env()`` call
2. **Document the environment variable** in this file
3. **Override in environment files** if needed (local.py, production.py)
4. **Add to .env.example** for team reference

Example:

.. code-block:: python

    # config/settings/base.py
    MY_FEATURE_ENABLED = env.bool("MY_FEATURE_ENABLED", default=False)
    MY_API_KEY = env("MY_API_KEY", default="")
    MY_MAX_RETRIES = env.int("MY_MAX_RETRIES", default=3)

See Also
--------

- :doc:`local-setup` --- Getting started with local development
