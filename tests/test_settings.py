"""Settings-level assertions about degrading to the capabilities provisioned.

These run in a subprocess because they need Django to boot with a different
environment than the one this test session was started with.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

from django.conf import settings
from django.db import connection

BASE_DIR = Path(__file__).resolve().parent.parent
MANIFEST = BASE_DIR / "app.json"

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


PROTOTYPE_BOOT = """
import django
django.setup()

from django.conf import settings
from django.test import Client

# No key-value store is attached, so the cache is in-process and dispatch is
# inline. Sessions stay in the database — the cache would lose them on restart.
assert settings.CACHES["default"]["BACKEND"] == (
    "django.core.cache.backends.locmem.LocMemCache"
), settings.CACHES
assert settings.CELERY_TASK_ALWAYS_EAGER is True
assert settings.SESSION_ENGINE == "django.contrib.sessions.backends.db"

# No transactional email and no error reporting are provisioned either.
assert settings.EMAIL_BACKEND == (
    "django.core.mail.backends.console.EmailBackend"
), settings.EMAIL_BACKEND
assert "anymail" not in settings.INSTALLED_APPS

# The manifest generates this, and a generated secret carries no trailing slash.
assert settings.ADMIN_URL.endswith("/"), settings.ADMIN_URL

response = Client(headers={"host": "prototype.herokuapp.com"}).get(
    "/healthz/", secure=True
)
assert response.status_code == 200, response.status_code
"""


def manifest_environment():
    """The config an app provisioned from app.json actually boots with.

    Anything the manifest leaves to the operator is deliberately left unset, so
    a variable that creeps back into being required fails this test.
    """
    environment = {}
    for name, spec in json.loads(MANIFEST.read_text())["env"].items():
        if "value" in spec:
            environment[name] = spec["value"]
        elif "generator" in spec:
            # Heroku substitutes a random secret; shape matters, not the value.
            environment[name] = "0f1e2d3c4b5a69788796a5b4c3d2e1f0"
    return environment


def test_an_app_provisioned_from_the_manifest_boots(db):
    """Provisioning is one command, so the manifest has to be enough on its own."""
    postgres = connection.settings_dict
    host = postgres["HOST"] or "localhost"
    port = postgres["PORT"] or "5432"
    env = {
        # Built from nothing, so no Redis, Mailgun or Sentry variable that
        # happens to be in this shell can prop the boot up.
        "PATH": os.environ["PATH"],
        "PYTHONPATH": str(BASE_DIR),
        "DJANGO_READ_DOT_ENV_FILE": "False",
        "DATABASE_URL": (
            f"postgres://{postgres['USER']}:{postgres['PASSWORD']}"
            f"@{host}:{port}/{postgres['NAME']}"
        ),
        **manifest_environment(),
    }
    result = subprocess.run(  # noqa: S603
        [sys.executable, "-c", PROTOTYPE_BOOT],
        cwd=BASE_DIR,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
