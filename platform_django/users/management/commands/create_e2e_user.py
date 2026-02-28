"""Management command to create an E2E test user.

This command creates a test user for Playwright E2E tests with email/password login.
The command is idempotent - safe to run multiple times.

Usage:
    python manage.py create_e2e_user
    python manage.py create_e2e_user --password=custom-password
"""

import os

from django.core.management.base import BaseCommand

from platform_django.users.models import User


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
                "(default: from E2E_USER_PASSWORD env var or 'e2e-test-password')"
            ),
        )

    def handle(self, *args, **options):
        email = options["email"]
        password = options["password"] or os.environ.get(
            "E2E_USER_PASSWORD", "e2e-test-password"
        )

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

        if created:
            self.stdout.write(self.style.SUCCESS(f"Created E2E test user: {email}"))
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"E2E test user already exists: {email} (password updated)"
                )
            )
