"""Every page Django renders from a template takes its CSS from the Vite build.

This is the one part of that wiring with no visual signal. ``DEBUG`` takes the
other branch of ``django-vite`` — the dev server's URL, spelled out rather than
looked up — so a broken manifest reference is invisible in every environment
anyone actually looks at the pages in, and shows up as an unstyled sign-in page
on a deploy (ADR-0012).
"""

import json
import re

import pytest
from django_vite.core.asset_loader import DjangoViteAssetLoader

STYLESHEET = "assets/django-0f1e2d3c.css"


@pytest.fixture
def built(tmp_path, settings):
    """Stand in for a production build, so this suite needs no frontend build."""
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {"django.css": {"file": STYLESHEET, "src": "django.css", "isEntry": True}}
        )
    )
    settings.DJANGO_VITE = {
        "platform_django": {
            "dev_mode": False,
            "static_url_prefix": "platform_django",
            "manifest_path": str(manifest),
        },
    }
    DjangoViteAssetLoader._instance = None  # noqa: SLF001
    yield
    DjangoViteAssetLoader._instance = None  # noqa: SLF001


@pytest.mark.django_db
def test_sign_in_page_links_the_built_stylesheet(client, built):
    html = client.get("/accounts/login/").content.decode()

    link = re.search(r'<link[^>]*rel="stylesheet"[^>]*>', html)

    assert link, "The sign-in page carries no stylesheet at all."
    assert STYLESHEET in link.group(), (
        f"Expected the manifest's hashed stylesheet in {link.group()}. A missing "
        "hash means the manifest was not consulted, so a deploy would serve a "
        "stale file or none."
    )


@pytest.mark.django_db
def test_the_stylesheet_is_a_link_and_not_a_script(client, built):
    """``{% vite_asset %}`` emits a <script type="module"> for a CSS entry.

    It does so only when dev_mode is off, and the browser refuses it on MIME
    type — which is the whole reason base.html spells the <link> out around
    ``{% vite_asset_url %}``.
    """
    html = client.get("/accounts/login/").content.decode()

    assert STYLESHEET not in re.sub(r"<link[^>]*>", "", html)


@pytest.mark.django_db
def test_nothing_is_fetched_from_a_cdn_any_more(client, built):
    assert "cdnjs" not in client.get("/accounts/login/").content.decode()
