"""Resolve connection URLs from environment primitives.

Pure functions over an environment mapping: nothing is imported from Django and
no state is held, so this is unit-testable without loading settings.

A supplied URL always wins, so platforms that inject one keep working. Absent
one, the URL is composed from the primitives the environment template carries.

Redis is an optional capability rather than a requirement: with none configured
the cache is in-process and task dispatch is eager, so a prototype runs without
paying for one and graduates by provisioning the add-on — no code change.
"""

from collections.abc import Mapping
from urllib.parse import quote


def _required_pg(env: Mapping[str, str], key: str) -> str:
    value = env.get(key)
    if not value:
        msg = f"Set DATABASE_URL, or the {key} primitive it is composed from."
        raise ValueError(msg)
    return value


def database_url(env: Mapping[str, str]) -> str:
    """Return the database connection URL for ``env``."""
    supplied = env.get("DATABASE_URL")
    if supplied:
        return supplied

    user = quote(_required_pg(env, "POSTGRES_USER"), safe="")
    password = quote(_required_pg(env, "POSTGRES_PASSWORD"), safe="")
    name = _required_pg(env, "POSTGRES_DB")
    host = env.get("POSTGRES_HOST") or "localhost"
    port = env.get("POSTGRES_PORT") or "5432"
    return f"postgres://{user}:{password}@{host}:{port}/{name}"


def redis_url(env: Mapping[str, str]) -> str | None:
    """Return the Redis connection URL for ``env``, or ``None`` if unconfigured.

    A port or index alone says nothing about where Redis is, so a host is what
    makes it configured.
    """
    supplied = env.get("REDIS_URL")
    if supplied:
        return supplied

    host = env.get("REDIS_HOST")
    if not host:
        return None

    port = env.get("REDIS_PORT") or "6379"
    index = env.get("REDIS_DB") or "0"
    return f"redis://{host}:{port}/{index}"


def project_slug(env: Mapping[str, str]) -> str:
    """Return the slug naming this project's resources.

    One Redis serves every project on a development machine, and a logical index
    is only ever handed out within a project — two projects both start at index
    0. The slug is therefore what keeps their cached values and queued tasks
    apart, rather than the index they happen to share.
    """
    return env.get("PROJECT_SLUG") or "app"


def project_display_name(env: Mapping[str, str]) -> str:
    """Return the name a user of this project sees.

    Separate from the slug because the two are wanted in different places: the
    slug names resources and has to survive being a database identifier, while
    this appears in a page title, an email and the API schema. Falling back to
    the slug means a project that set only the slug still reads as itself
    rather than as the template it was cloned from.
    """
    supplied = env.get("PROJECT_DISPLAY_NAME")
    if supplied:
        return supplied

    return project_slug(env).replace("_", " ").replace("-", " ").title()


def cache_config(env: Mapping[str, str]) -> dict[str, dict]:
    """Return the ``CACHES`` setting for ``env``."""
    url = redis_url(env)
    # Applied at both tiers, so a key is named the same whether or not Redis has
    # been provisioned and graduating cannot quietly change what is cached.
    key_prefix = project_slug(env)

    if not url:
        return {
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "KEY_PREFIX": key_prefix,
            },
        }

    return {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": url,
            "KEY_PREFIX": key_prefix,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                # Mimicking memcache behavior.
                # https://github.com/jazzband/django-redis#memcached-exceptions-behavior
                "IGNORE_EXCEPTIONS": True,
            },
        },
    }


def task_always_eager(env: Mapping[str, str]) -> bool:
    """Return whether task dispatch should run inline for ``env``.

    With no broker, dispatching a task would otherwise hang.
    """
    return redis_url(env) is None
