"""REFERENCE PATTERN — do not delete as redundant.

``tests/api/test_views.py`` already proves the scope holds over HTTP, so this
file is not load-bearing for correctness. It is the worked example the skills
point at for a focused selector test: assert the access scope directly, so that
a widened query fails here with an obvious message rather than as a 404 that
turned into a 200 somewhere downstream.

The shape to copy: create a record the caller must not see, then assert it is
absent from the selector's result.
"""

import pytest

from platform_django.users.models import User
from platform_django.users.selectors import user_list_visible_to
from platform_django.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


def test_user_list_visible_to_includes_the_viewer(user: User):
    assert user in user_list_visible_to(user.pk)


def test_user_list_visible_to_excludes_everyone_else(user: User):
    other: User = UserFactory()  # type: ignore[assignment]

    assert other not in user_list_visible_to(user.pk)
