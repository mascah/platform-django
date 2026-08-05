"""The landing page's contract: one document, the same for every visitor.

Two guarantees hold it together, and each is easy to break by accident.

The page authorises its one inline script by hash rather than by the nonce
every other route uses, because a nonce is unique per response and the script
has to be able to run from a document that was not rendered for this visitor.
The hash and the script therefore have to change together, and the first test
here is what makes that true.

And the bytes must not depend on who is asking. The browser learns whether
somebody is signed in from a hint cookie, never from the document.
"""

import base64
import hashlib
from pathlib import Path

import pytest
from csp.constants import NONCE
from django.contrib.sessions.models import Session

from config.middleware import SESSION_HINT_COOKIE
from platform_django.users.tests.factories import UserFactory

BASE_DIR = Path(__file__).resolve().parent.parent
SNIPPET = BASE_DIR / "apps" / "landing" / "src" / "session-hint.js"


@pytest.fixture
def landing_page(tmp_path, settings):
    """Stand in for a built landing page, so this suite needs no frontend build.

    Only the document's headers and its invariance are under test here; what
    the browser does with the markup is the Playwright suite's job.
    """
    (tmp_path / "index.html").write_text("<!doctype html><html lang='en'></html>")
    settings.DEBUG = False
    settings.STATIC_ROOT = str(tmp_path)
    return tmp_path


def _script_src(response):
    policy = response.headers["Content-Security-Policy"]
    return next(d for d in policy.split(";") if d.strip().startswith("script-src"))


def test_policy_hash_matches_the_shipped_snippet(settings):
    """The whole no-flash design rests on these two staying in step.

    Nothing at runtime notices when they part company: the browser simply
    refuses to run the script, and the landing page quietly shows a signed-in
    visitor the wrong call to action. This is the thing that notices.
    """
    digest = base64.b64encode(hashlib.sha256(SNIPPET.read_bytes()).digest()).decode()

    assert f"'sha256-{digest}'" == settings.LANDING_SCRIPT_HASH, (
        f"{SNIPPET.relative_to(BASE_DIR)} changed without LANDING_SCRIPT_HASH. "
        f"Set it to 'sha256-{digest}'."
    )


@pytest.mark.django_db
def test_landing_page_authorises_its_script_by_hash_not_nonce(client, landing_page):
    script_src = _script_src(client.get("/"))

    assert "sha256-" in script_src
    assert "nonce-" not in script_src, (
        "A nonce is unique per response, so a document carrying one cannot be "
        "cached by anything."
    )


@pytest.mark.django_db
def test_the_hash_is_scoped_to_the_landing_page(client, settings):
    """Everywhere else keeps the nonce-based policy, untouched.

    django-csp only writes a nonce into the header when a view actually reads
    ``request.csp_nonce``, so the header of a page that uses none is not
    evidence either way. What matters is that the landing page's hash is not
    handed to the rest of the site, and that the nonce is still on offer there.
    """
    assert settings.LANDING_SCRIPT_HASH not in _script_src(client.get("/about/"))
    assert NONCE in settings.CONTENT_SECURITY_POLICY["DIRECTIVES"]["script-src"]


@pytest.mark.django_db
def test_document_is_byte_identical_for_a_signed_in_visitor(client, landing_page):
    """The only difference between two visitors is the cookie they send."""
    anonymous = client.get("/").content

    client.force_login(UserFactory())

    assert client.get("/").content == anonymous


@pytest.mark.django_db
def test_hint_appears_once_somebody_is_signed_in(client):
    client.get("/healthz/")
    assert SESSION_HINT_COOKIE not in client.cookies

    client.force_login(UserFactory())
    client.get("/healthz/")

    hint = client.cookies[SESSION_HINT_COOKIE]
    assert hint.value == "1"
    assert not hint["httponly"], "The page reads this from JavaScript before paint."


@pytest.mark.django_db
def test_hint_clears_when_the_session_ends_anywhere_at_all(client):
    """Signing out in another tab, or a session simply expiring, is not a logout.

    Reconciling on every response rather than at logout is the only reason this
    recovers — which is why the cookie comes from middleware and not from an
    auth signal or an allauth hook. Destroying the session server-side stands in
    for every way a session can end without this browser being told.
    """
    client.force_login(UserFactory())
    client.get("/healthz/")
    assert client.cookies[SESSION_HINT_COOKIE].value == "1"

    Session.objects.all().delete()
    cleared = client.get("/healthz/").cookies[SESSION_HINT_COOKIE]

    assert cleared.value == ""
    assert int(cleared["max-age"]) == 0
