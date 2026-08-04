"""Management command to create an E2E test user.

This command creates a test user for Playwright E2E tests with email/password
login. It is also what seeds a Preview, so the account it creates has to be
usable under production settings, where ``ACCOUNT_EMAIL_VERIFICATION`` is
``mandatory``.

The command is idempotent - safe to run multiple times.

Usage:
    python manage.py create_e2e_user
    python manage.py create_e2e_user --password=custom-password
"""

import os

from allauth.account.models import EmailAddress
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from platform_django.users.models import User

DEFAULT_PASSWORD = "e2e-test-password"  # noqa: S105


class Command(BaseCommand):
    help = "Create an E2E test user for Playwright tests"

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            type=str,
            default="e2e@test.local",
            help="Email for the test user (default: e2e@test.local)",
        )
        parser.add_argument(
            "--password",
            type=str,
            default=None,
            help=(
                "Password for the test user "
                "(default: from E2E_USER_PASSWORD env var, or the built-in "
                "password when DEBUG is on)"
            ),
        )

    def handle(self, *args, **options):
        email = options["email"]
        password = options["password"] or os.environ.get("E2E_USER_PASSWORD")

        # A Preview is on the public internet, so falling back to the built-in
        # password there would publish a working credential. Only a run with
        # DEBUG on may use it.
        if not password:
            if not settings.DEBUG:
                msg = (
                    "Refusing to use the built-in password with DEBUG off. Set "
                    "E2E_USER_PASSWORD - for a Preview, as a review app config "
                    "var on the pipeline - or pass --password."
                )
                raise CommandError(msg)
            password = DEFAULT_PASSWORD

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": email.split("@")[0],
                "name": "E2E Test User",
                "is_active": True,
            },
        )

        # Always update the password to ensure it's correct
        user.set_password(password)
        user.save(update_fields=["password"])

        # Without a verified address allauth blocks login wherever
        # ACCOUNT_EMAIL_VERIFICATION is mandatory - which is everywhere except
        # local settings - and mails the confirmation link to whatever the email
        # backend is. On a Preview that is the dyno log.
        EmailAddress.objects.update_or_create(
            user=user,
            email=email,
            defaults={"verified": True, "primary": True},
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created E2E test user: {email}"))
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"E2E test user already exists: {email} (password updated)"
                )
            )
