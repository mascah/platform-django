"""Unit tests for connection URL resolution — no Django settings involved."""

import pytest

from config.env import cache_config
from config.env import database_url
from config.env import redis_url
from config.env import task_always_eager

PRIMITIVES = {
    "POSTGRES_HOST": "db.example.com",
    "POSTGRES_PORT": "5433",
    "POSTGRES_DB": "shop",
    "POSTGRES_USER": "shopkeeper",
    "POSTGRES_PASSWORD": "s3cret",
}


def test_database_url_composed_from_primitives():
    assert (
        database_url(PRIMITIVES)
        == "postgres://shopkeeper:s3cret@db.example.com:5433/shop"
    )


def test_supplied_database_url_wins():
    supplied = "postgres://someone:else@platform.example.com:6000/injected"
    assert database_url({**PRIMITIVES, "DATABASE_URL": supplied}) == supplied


def test_database_url_defaults_host_and_port():
    primitives = {
        k: v for k, v in PRIMITIVES.items() if not k.endswith(("HOST", "PORT"))
    }
    assert (
        database_url(primitives) == "postgres://shopkeeper:s3cret@localhost:5432/shop"
    )


def test_database_url_escapes_credentials():
    assert database_url({**PRIMITIVES, "POSTGRES_PASSWORD": "p@ss/word"}) == (
        "postgres://shopkeeper:p%40ss%2Fword@db.example.com:5433/shop"
    )


@pytest.mark.parametrize(
    "missing", ["POSTGRES_DB", "POSTGRES_USER", "POSTGRES_PASSWORD"]
)
def test_database_url_requires_credentials(missing):
    with pytest.raises(ValueError, match=missing):
        database_url({k: v for k, v in PRIMITIVES.items() if k != missing})


def test_redis_url_composed_from_primitives():
    assert (
        redis_url(
            {"REDIS_HOST": "cache.example.com", "REDIS_PORT": "6380", "REDIS_DB": "3"}
        )
        == "redis://cache.example.com:6380/3"
    )


def test_supplied_redis_url_wins():
    supplied = "rediss://platform.example.com:6379/9"
    assert (
        redis_url({"REDIS_HOST": "cache.example.com", "REDIS_URL": supplied})
        == supplied
    )


def test_redis_url_defaults_port_and_index():
    assert redis_url({"REDIS_HOST": "cache.example.com"}) == (
        "redis://cache.example.com:6379/0"
    )


def test_redis_url_absent_when_nothing_configured():
    assert redis_url({}) is None
    assert redis_url({"REDIS_PORT": "6379", "REDIS_DB": "0"}) is None


def test_cache_is_in_process_without_redis():
    assert cache_config({}) == {
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
    }


def test_cache_uses_redis_when_configured():
    default = cache_config({"REDIS_HOST": "cache.example.com"})["default"]
    assert default["BACKEND"] == "django_redis.cache.RedisCache"
    assert default["LOCATION"] == "redis://cache.example.com:6379/0"


def test_task_dispatch_is_eager_only_without_redis():
    assert task_always_eager({}) is True
    assert task_always_eager({"REDIS_URL": "redis://localhost:6379/0"}) is False
