"""The API is exercised through DRF's client, not by constructing the viewset.

A read of another user's record proves the selector scoped the queryset; a
PATCH that survives ``refresh_from_db`` proves the service performed the write.
Neither test imports ``services`` or ``selectors``.
"""

from http import HTTPStatus

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from platform_django.users.models import User
from platform_django.users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client(user: User) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=user)
    return client


class TestUserViewSetReads:
    def test_list_returns_only_the_requesting_user(
        self,
        user: User,
        api_client: APIClient,
    ):
        UserFactory()  # another user, which must not appear

        response = api_client.get(reverse("api:user-list"))

        assert response.status_code == HTTPStatus.OK
        assert [row["username"] for row in response.data["results"]] == [user.username]

    def test_another_users_record_is_not_found(self, api_client: APIClient):
        other: User = UserFactory()  # type: ignore[assignment]

        response = api_client.get(
            reverse("api:user-detail", kwargs={"username": other.username}),
        )

        assert response.status_code == HTTPStatus.NOT_FOUND

    def test_me_returns_the_requesting_user(self, user: User, api_client: APIClient):
        response = api_client.get(reverse("api:user-me"))

        assert response.status_code == HTTPStatus.OK
        assert response.data == {
            "username": user.username,
            "url": f"http://testserver/api/users/{user.username}/",
            "name": user.name,
            "email": user.email,
            "id": user.id,
        }


class TestUserViewSetWrites:
    def test_put_persists_every_writable_field(self, user: User, api_client: APIClient):
        # The service is handed the serializer's validated_data wholesale, so a
        # writable field the service does not accept would fail here and only
        # here.
        response = api_client.put(
            reverse("api:user-detail", kwargs={"username": user.username}),
            {
                "username": "ada",
                "name": "Ada Lovelace",
                "email": "ada@example.com",
            },
            format="json",
        )

        assert response.status_code == HTTPStatus.OK
        user.refresh_from_db()
        assert user.username == "ada"
        assert user.name == "Ada Lovelace"
        assert user.email == "ada@example.com"
        assert response.data["url"].endswith("/api/users/ada/")

    def test_patch_persists_the_new_name(self, user: User, api_client: APIClient):
        response = api_client.patch(
            reverse("api:user-detail", kwargs={"username": user.username}),
            {"name": "Ada Lovelace"},
            format="json",
        )

        assert response.status_code == HTTPStatus.OK
        user.refresh_from_db()
        assert user.name == "Ada Lovelace"

    def test_patch_leaves_unsupplied_fields_alone(
        self,
        user: User,
        api_client: APIClient,
    ):
        original_email = user.email

        api_client.patch(
            reverse("api:user-detail", kwargs={"username": user.username}),
            {"name": "Ada Lovelace"},
            format="json",
        )

        user.refresh_from_db()
        assert user.email == original_email

    def test_another_users_record_cannot_be_written(self, api_client: APIClient):
        other: User = UserFactory()  # type: ignore[assignment]

        response = api_client.patch(
            reverse("api:user-detail", kwargs={"username": other.username}),
            {"name": "Ada Lovelace"},
            format="json",
        )

        assert response.status_code == HTTPStatus.NOT_FOUND
        other.refresh_from_db()
        assert other.name != "Ada Lovelace"
