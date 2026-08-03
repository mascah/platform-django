"""REFERENCE PATTERN — do not delete as redundant.

The HTTP tests in ``test_views.py`` and ``tests/api/test_views.py`` already
cover this behaviour, so this file is not load-bearing for correctness. It is
load-bearing as an example: the skills instruct agents to write a focused
service test that asserts persisted state, and a worked module that contradicts
its own guidance is worse than a little duplication.

The shape to copy: call the service, then assert against the database — not
against the return value alone, which would pass even if nothing was saved.
"""

import pytest

from platform_django.users.models import User
from platform_django.users.services import user_update_profile

pytestmark = pytest.mark.django_db


def test_user_update_profile_persists_the_new_name(user: User):
    user_update_profile(user_id=user.pk, name="Ada Lovelace")

    user.refresh_from_db()
    assert user.name == "Ada Lovelace"


def test_user_update_profile_leaves_unsupplied_fields_alone(user: User):
    original_email = user.email

    user_update_profile(user_id=user.pk, name="Ada Lovelace")

    user.refresh_from_db()
    assert user.email == original_email
