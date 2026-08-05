"""Views are exercised through the HTTP boundary, not by constructing them.

These tests describe what a caller can observe: a status code, a redirect
target, a persisted change. They do not import ``services`` or ``selectors``,
so moving logic between a view and a service is a refactor rather than a test
rewrite.
"""

from http import HTTPStatus

import pytest
from django.conf import settings
from django.test import Client
from django.urls import reverse

from platform_django.users.models import User
from platform_django.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestUserDetailView:
    def test_renders_for_an_authenticated_visitor(self, user: User, client: Client):
        visitor: User = UserFactory()  # type: ignore[assignment]
        client.force_login(visitor)

        response = client.get(
            reverse("users:detail", kwargs={"username": user.username}),
        )

        assert response.status_code == HTTPStatus.OK

    def test_redirects_an_anonymous_visitor_to_login(self, user: User, client: Client):
        url = reverse("users:detail", kwargs={"username": user.username})

        response = client.get(url)

        assert response.status_code == HTTPStatus.FOUND
        assert response["Location"] == f"{reverse(settings.LOGIN_URL)}?next={url}"


class TestLoginEntrance:
    def test_sends_an_already_signed_in_visitor_to_the_application(
        self, user: User, client: Client
    ):
        """The landing page links here unconditionally, so this is the loop.

        allauth's ``RedirectAuthenticatedUserMixin`` bounces a signed-in visitor
        to ``LOGIN_REDIRECT_URL``. Pointing that at ``/`` returned them to the
        landing page they had just clicked Sign In on.
        """
        client.force_login(user)

        response = client.get(reverse("account_login"))

        assert response.status_code == HTTPStatus.FOUND
        assert response["Location"] == "/app/"


class TestUserRedirectView:
    def test_redirects_to_the_visitors_own_detail_page(
        self, user: User, client: Client
    ):
        client.force_login(user)

        response = client.get(reverse("users:redirect"))

        assert response.status_code == HTTPStatus.FOUND
        assert response["Location"] == f"/users/{user.username}/"


class TestUserUpdateView:
    def test_persists_the_new_name(self, user: User, client: Client):
        client.force_login(user)

        response = client.post(reverse("users:update"), {"name": "Ada Lovelace"})

        assert response.status_code == HTTPStatus.FOUND
        assert response["Location"] == f"/users/{user.username}/"
        user.refresh_from_db()
        assert user.name == "Ada Lovelace"

    def test_reports_success(self, user: User, client: Client):
        client.force_login(user)

        response = client.post(
            reverse("users:update"),
            {"name": "Ada Lovelace"},
            follow=True,
        )

        assert [str(m) for m in response.context["messages"]] == [
            "Information successfully updated",
        ]

    def test_redirects_an_anonymous_visitor_to_login(self, client: Client):
        response = client.post(reverse("users:update"), {"name": "Ada Lovelace"})

        assert response.status_code == HTTPStatus.FOUND
        assert response["Location"].startswith(reverse(settings.LOGIN_URL))
