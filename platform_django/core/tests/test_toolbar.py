"""The toolbar's visibility rule, which the browser suite depends on."""

from platform_django.core.toolbar import show_toolbar


def test_hidden_from_the_browser_suite(rf, settings):
    """A handle over the page swallows clicks aimed at what sits beneath it."""
    settings.DEBUG = True
    settings.INTERNAL_IPS = ["127.0.0.1"]
    request = rf.get("/", headers={"x-playwright-test": "1"}, REMOTE_ADDR="127.0.0.1")

    assert show_toolbar(request) is False


def test_shown_to_a_person(rf, settings):
    """Suppressing it for Playwright must not suppress it for development."""
    settings.DEBUG = True
    settings.INTERNAL_IPS = ["127.0.0.1"]
    request = rf.get("/", REMOTE_ADDR="127.0.0.1")

    assert show_toolbar(request) is True
