"""What ``allauth/elements/fields.html`` owes the forms it draws.

Every authentication form on screen used to be drawn by crispy-bootstrap5;
now the project's own ``field.html`` draws all of them, through the loop in
``fields.html``. Two of the things crispy did for free are load-bearing and
nothing else notices when they stop.
"""

import re

import pytest


@pytest.mark.django_db
def test_a_rejected_password_is_not_written_back_into_the_page(client):
    """``field.html`` renders the input itself, so the widget never sees it.

    ``PasswordInput`` defaults to ``render_value=False`` precisely to keep a
    submitted password out of the markup; bypassing the widget means that
    default protects nothing, and a failed sign-in would put the password in
    the page source, the back-forward cache and any HTML capture.
    """
    password = "correct-horse-battery-staple"  # noqa: S105

    html = client.post(
        "/accounts/login/", {"login": "nobody", "password": password}
    ).content.decode()

    assert "id_password" in html, "The form did not re-render; nothing was proved."
    assert password not in html


@pytest.mark.django_db
def test_the_sign_in_fields_keep_their_labels(client):
    """allauth asks for ``unlabeled=True`` here and the label is kept anyway.

    ``e2e/auth/auth.setup.ts`` signs in with ``getByLabel('Username')``, so
    dropping the label takes the whole browser suite with it — and an input
    whose only name is a placeholder has no accessible name once it has
    content.
    """
    html = client.get("/accounts/login/").content.decode()

    for field_id, label in [("id_login", "Username"), ("id_password", "Password")]:
        pattern = rf'<label[^>]*for="{field_id}"[^>]*>\s*{label}\s*</label>'
        assert re.search(pattern, html), f"No label for {field_id} reading {label}."


@pytest.mark.django_db
def test_a_field_error_reaches_the_page(client):
    """The override carried no ``errors`` at all; crispy was rendering them."""
    html = client.post("/accounts/signup/", {"email": "not-an-email"}).content.decode()

    assert "Enter a valid email address." in html
