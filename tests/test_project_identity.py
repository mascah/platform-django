"""Project identity reaches the places a user actually reads it.

config/env.py resolves the display name; these check it arrives — in a rendered
page and in the API schema — because a value nothing consumes is not identity.
"""

from pathlib import Path

import pytest
from django.template import Context
from django.template import RequestContext
from django.template import Template
from django.test import RequestFactory
from django.test import override_settings

DISPLAY_NAME = "ACME Rocket Sled"
TEMPLATES = Path(__file__).resolve().parent.parent / "platform_django" / "templates"
TITLED_TEMPLATES = (
    TEMPLATES / "base.html",
    TEMPLATES / "apps" / "platform_django.html",
)


@override_settings(PROJECT_DISPLAY_NAME=DISPLAY_NAME)
def test_display_name_is_available_to_every_template():
    """Via the context processor, so no view has to remember to pass it."""
    request = RequestFactory().get("/")
    rendered = Template("{{ project_display_name }}").render(RequestContext(request))

    assert rendered == DISPLAY_NAME


@pytest.mark.parametrize("template", TITLED_TEMPLATES, ids=lambda path: path.name)
def test_templates_title_themselves_from_the_display_name(template: Path):
    """Templates must read the variable rather than a hardcoded name."""
    source = template.read_text()

    assert "{{ project_display_name }}" in source
    assert "Platform Django" not in source


def test_settings_derive_names_from_identity_rather_than_the_template(settings):
    """The two values are the only difference between one project and the next."""
    assert (
        settings.SPECTACULAR_SETTINGS["TITLE"] == f"{settings.PROJECT_DISPLAY_NAME} API"
    )
    # The slug names resources; the display name never does.
    assert settings.CELERY_TASK_DEFAULT_QUEUE == settings.PROJECT_SLUG


def test_rendering_a_template_without_a_request_still_works():
    """Context processors only run with a request; nothing may depend on them."""
    assert Template("{{ project_display_name }}").render(Context()) == ""
