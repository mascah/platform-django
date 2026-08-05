"""
With these settings, tests run faster.
"""

from .base import *  # noqa: F403
from .base import DJANGO_VITE
from .base import TEMPLATES
from .base import env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="CYoSqCyCx6kuujEOcDLvBCgx85RkMuWoEM5b3ldUB3KBxvC5kd9VeCJBjwOTZNrR",
)
# https://docs.djangoproject.com/en/dev/ref/settings/#test-runner
TEST_RUNNER = "django.test.runner.DiscoverRunner"

# PASSWORDS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# CACHES
# ------------------------------------------------------------------------------
# Tests never reach for a real Redis, whatever the environment has configured.
CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
}

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# DEBUGGING FOR TEMPLATES
# ------------------------------------------------------------------------------
TEMPLATES[0]["OPTIONS"]["debug"] = True  # type: ignore[index]

# MEDIA
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = "http://media.testserver/"

# django-vite
# ------------------------------------------------------------------------------
# Since base.html links the stylesheet Vite builds (ADR-0012), every page
# Django renders from a template now reaches django-vite. The suite does not
# build the frontend, and requiring it to would put a Node build in front of
# every Python test; dev_mode makes the tags construct a URL rather than read a
# manifest, so a page renders either way.
#
# Which leaves the manifest path untested, and it is the one part with no
# visual signal — so tests/test_server_rendered_styles.py turns dev_mode back
# off against a manifest of its own.
for _app_config in DJANGO_VITE.values():
    _app_config["dev_mode"] = True

# Your stuff...
# ------------------------------------------------------------------------------
