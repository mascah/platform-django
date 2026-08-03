from csp.constants import NONCE

from config.settings.base import *  # noqa: F403
from config.settings.base import DJANGO_VITE
from config.settings.base import INSTALLED_APPS
from config.settings.base import MIDDLEWARE
from config.settings.base import env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = True
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="huldAQEdv35LFtPDGq0NKFKOfnx41S7FaqCLqm8d0MTQzGVaLt9xviyRwSaHEaOG",
)
# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ["localhost", "0.0.0.0", "127.0.0.1"]  # noqa: S104

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = env(
    "EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)
# https://docs.djangoproject.com/en/dev/ref/settings/#email-host
EMAIL_HOST = env("EMAIL_HOST", default="mailpit")
# https://docs.djangoproject.com/en/dev/ref/settings/#email-port
EMAIL_PORT = 1025

# WhiteNoise
# ------------------------------------------------------------------------------
# http://whitenoise.evans.io/en/latest/django.html#using-whitenoise-in-development
INSTALLED_APPS = ["whitenoise.runserver_nostatic", *INSTALLED_APPS]


# django-debug-toolbar
# ------------------------------------------------------------------------------
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#prerequisites
INSTALLED_APPS += ["debug_toolbar"]
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#middleware
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
# https://django-debug-toolbar.readthedocs.io/en/latest/configuration.html#debug-toolbar-config
DEBUG_TOOLBAR_CONFIG = {
    "DISABLE_PANELS": [
        "debug_toolbar.panels.redirects.RedirectsPanel",
        # Disable profiling panel due to an issue with Python 3.12+:
        # https://github.com/jazzband/django-debug-toolbar/issues/1875
        "debug_toolbar.panels.profiling.ProfilingPanel",
    ],
    "SHOW_TEMPLATE_CONTEXT": True,
}
# https://django-debug-toolbar.readthedocs.io/en/latest/installation.html#internal-ips
INTERNAL_IPS = ["127.0.0.1", "10.0.2.2"]
if env("USE_DOCKER") == "yes":
    import socket

    hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
    INTERNAL_IPS += [".".join([*ip.split(".")[:-1], "1"]) for ip in ips]

# django-extensions
# ------------------------------------------------------------------------------
# https://django-extensions.readthedocs.io/en/latest/installation_instructions.html#configuration
INSTALLED_APPS += ["django_extensions"]
# Celery
# ------------------------------------------------------------------------------
# https://docs.celeryq.dev/en/stable/userguide/configuration.html#task-eager-propagates
CELERY_TASK_EAGER_PROPAGATES = True

# django-vite
# ------------------------------------------------------------------------------
# Enable dev_mode for all Vite apps (can be disabled in CI while keeping DEBUG=True)
DJANGO_VITE_DEV_MODE = env.bool("DJANGO_VITE_DEV_MODE", DEBUG)
for app_name in DJANGO_VITE:
    DJANGO_VITE[app_name]["dev_mode"] = DJANGO_VITE_DEV_MODE

# Content Security Policy - relaxed for development with Vite HMR
# Dynamically allows all Vite dev servers configured in DJANGO_VITE
_vite_dev_servers = []
_vite_ws_servers = []
for app_config in DJANGO_VITE.values():
    port = app_config.get("dev_server_port", 5173)
    _vite_dev_servers.append(f"http://localhost:{port}")
    _vite_ws_servers.append(f"ws://localhost:{port}")

CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": ("'none'",),
        "script-src": (
            "'self'",
            NONCE,
            "https://internal-j.posthog.com",
            "https://cdnjs.cloudflare.com",
            *_vite_dev_servers,
        ),
        "style-src": (
            "'self'",
            "'unsafe-inline'",
            "https://rsms.me",
            "https://cdnjs.cloudflare.com",
        ),
        "img-src": ("'self'", "data:"),
        "font-src": ("'self'", "https://rsms.me"),
        "connect-src": (
            "'self'",
            "https://us.posthog.com",
            "https://us.i.posthog.com",
            "https://internal-j.posthog.com",
            "https://cdnjs.cloudflare.com",
            *_vite_dev_servers,
            *_vite_ws_servers,
        ),
        "frame-ancestors": ("'none'",),
        "form-action": ("'self'",),
        "base-uri": ("'self'",),
        "object-src": ("'none'",),
    },
}

ACCOUNT_EMAIL_VERIFICATION = "optional"
