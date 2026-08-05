"""When django-debug-toolbar renders, for the settings that enable it."""

from django.conf import settings
from django.http import HttpRequest


def show_toolbar(request: HttpRequest) -> bool:
    """Hide the toolbar from the browser suite, show it to a person.

    The toolbar renders a fixed-position handle over the page, which swallows
    pointer events aimed at whatever sits beneath it. A Playwright click then
    retries until the test times out, and which test it lands on depends on
    where that page happens to put its controls — so it presents as a flake in
    something unrelated. ``e2e/fixtures.ts`` has always sent this header for
    exactly this reason; this is what reads it. CI runs the browser suite
    against ``config.settings.local`` from loopback, so the toolbar renders
    there too and this is not a local-only concern.

    The second clause restates django-debug-toolbar's own default rather than
    calling it: importing ``debug_toolbar`` needs the app installed, which is
    true wherever this callback runs but not under ``config.settings.test``,
    where the test below has to import this module.

    Lives here rather than in the settings module for the same reason — that
    module mutates the ``DJANGO_VITE`` dict it shares with ``base``, so
    importing it to reach this function would leak dev mode into the importer.
    """
    if request.headers.get("X-Playwright-Test"):
        return False
    # https://django-debug-toolbar.readthedocs.io/en/latest/configuration.html#show-toolbar-callback
    return settings.DEBUG and request.META.get("REMOTE_ADDR") in settings.INTERNAL_IPS
