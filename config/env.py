"""Resolve connection URLs from environment primitives.

Pure functions over an environment mapping: nothing is imported from Django and
no state is held, so this is unit-testable without loading settings.

A supplied URL always wins, so platforms that inject one keep working. Absent
one, the URL is composed from the primitives the environment template carries.
"""

from collections.abc import Mapping
from urllib.parse import quote


def _required(env: Mapping[str, str], key: str) -> str:
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

    user = quote(_required(env, "POSTGRES_USER"), safe="")
    password = quote(_required(env, "POSTGRES_PASSWORD"), safe="")
    name = _required(env, "POSTGRES_DB")
    host = env.get("POSTGRES_HOST") or "localhost"
    port = env.get("POSTGRES_PORT") or "5432"
    return f"postgres://{user}:{password}@{host}:{port}/{name}"


def redis_url(env: Mapping[str, str]) -> str:
    """Return the Redis connection URL for ``env``."""
    supplied = env.get("REDIS_URL")
    if supplied:
        return supplied

    host = env.get("REDIS_HOST") or "localhost"
    port = env.get("REDIS_PORT") or "6379"
    index = env.get("REDIS_DB") or "0"
    return f"redis://{host}:{port}/{index}"
