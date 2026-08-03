"""Settings-level assertions about degrading to no Redis.

The no-Redis case runs in a subprocess because it needs Django to boot with a
different environment than the one this test session was started with.
"""

import os
import subprocess
import sys
from pathlib import Path

from django.conf import settings
from django.db import connection

BASE_DIR = Path(__file__).resolve().parent.parent

DEGRADED_BOOT = """
import django
django.setup()

from django.conf import settings
from django.test import Client

assert settings.CACHES["default"]["BACKEND"] == (
    "django.core.cache.backends.locmem.LocMemCache"
), settings.CACHES
assert settings.CELERY_TASK_ALWAYS_EAGER is True
assert settings.SESSION_ENGINE == "django.contrib.sessions.backends.db"

response = Client(headers={"host": "localhost"}).get("/healthz/")
assert response.status_code == 200, response.status_code

# Dispatch runs inline rather than hanging on a broker that is not there.
from platform_django.users.tasks import get_users_count

assert isinstance(get_users_count.delay().get(), int)
"""


def test_sessions_stay_database_backed():
    """Moving sessions to the cache would log everyone out on restart."""
    assert settings.SESSION_ENGINE == "django.contrib.sessions.backends.db"


def test_boots_and_serves_a_request_with_no_redis(db):
    # Every request is wrapped in a transaction, so serving one needs the
    # database — but nothing here needs Redis.
    postgres = connection.settings_dict
    env = {k: v for k, v in os.environ.items() if not k.startswith("REDIS")}
    env |= {
        # Not config.settings.test, which pins an in-process cache of its own.
        "DJANGO_SETTINGS_MODULE": "config.settings.local",
        # The committed .env carries Redis primitives; ignore it entirely so
        # this really is the no-Redis case.
        "DJANGO_READ_DOT_ENV_FILE": "False",
        "POSTGRES_HOST": postgres["HOST"] or "localhost",
        "POSTGRES_PORT": str(postgres["PORT"] or "5432"),
        "POSTGRES_DB": postgres["NAME"],
        "POSTGRES_USER": postgres["USER"],
        "POSTGRES_PASSWORD": postgres["PASSWORD"],
        "USE_DOCKER": "no",
        "PYTHONPATH": str(BASE_DIR),
    }
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", DEGRADED_BOOT],
        cwd=BASE_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
