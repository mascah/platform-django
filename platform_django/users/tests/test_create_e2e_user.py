"""The seed command behind a Preview's only account.

Two things about it are load-bearing and neither is obvious from reading it:
the address it creates has to be verified, or allauth refuses the login
everywhere ``ACCOUNT_EMAIL_VERIFICATION`` is mandatory; and it must not fall
back to its built-in password on a host that is on the public internet.
"""

import pytest
from allauth.account.models import EmailAddress
from django.core.management import call_command
from django.core.management.base import CommandError

from platform_django.users.models import User

pytestmark = pytest.mark.django_db


def test_seeded_address_is_verified_so_allauth_permits_login():
    call_command("create_e2e_user", "--password=whatever")

    address = EmailAddress.objects.get(email="e2e@test.local")
    assert address.verified
    assert address.primary


def test_rerunning_leaves_one_verified_address():
    call_command("create_e2e_user", "--password=whatever")
    call_command("create_e2e_user", "--password=whatever")

    assert User.objects.filter(email="e2e@test.local").count() == 1
    assert EmailAddress.objects.filter(email="e2e@test.local").count() == 1


def test_refuses_the_built_in_password_when_debug_is_off(settings, monkeypatch):
    monkeypatch.delenv("E2E_USER_PASSWORD", raising=False)
    settings.DEBUG = False

    with pytest.raises(CommandError, match="E2E_USER_PASSWORD"):
        call_command("create_e2e_user")

    assert not User.objects.filter(email="e2e@test.local").exists()


def test_supplied_password_is_accepted_when_debug_is_off(settings, monkeypatch):
    monkeypatch.setenv("E2E_USER_PASSWORD", "from-the-config-var")
    settings.DEBUG = False

    call_command("create_e2e_user")

    user = User.objects.get(email="e2e@test.local")
    assert user.check_password("from-the-config-var")
