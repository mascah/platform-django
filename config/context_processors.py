"""Make project identity available to templates.

Django has no built-in way to read a setting from a template, and the display
name is wanted in the page title and the navigation brand of every page.
"""

from django.conf import settings
from django.http import HttpRequest


def project(request: HttpRequest) -> dict[str, str]:
    """Expose the name a user of this project sees."""
    return {"project_display_name": settings.PROJECT_DISPLAY_NAME}
