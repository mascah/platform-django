from django.contrib.auth.validators import UnicodeUsernameValidator
from django.urls import resolve
from django.urls import reverse

from platform_django.users.models import User


def test_user_detail(user: User):
    assert (
        reverse("api:user-detail", kwargs={"username": user.username})
        == f"/api/users/{user.username}/"
    )
    assert resolve(f"/api/users/{user.username}/").view_name == "api:user-detail"


def test_user_detail_accepts_every_character_the_username_validator_allows():
    """A dotted username has to round-trip, or /api/users/me/ 500s.

    UnicodeUsernameValidator allows "@", ".", "+", "-" and "_", and
    createsuperuser will happily take an email address at the username prompt.
    The router's default lookup regex excludes the dot.
    """
    username = "ada@example.com"
    UnicodeUsernameValidator()(username)  # the premise: Django accepts this

    url = reverse("api:user-detail", kwargs={"username": username})

    assert url == f"/api/users/{username}/"
    assert resolve(url).kwargs["username"] == username


def test_user_list():
    assert reverse("api:user-list") == "/api/users/"
    assert resolve("/api/users/").view_name == "api:user-list"


def test_user_me():
    assert reverse("api:user-me") == "/api/users/me/"
    assert resolve("/api/users/me/").view_name == "api:user-me"
