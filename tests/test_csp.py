"""What the browser is allowed to talk to, asserted where drift is invisible.

A blocked request is refused inside the renderer. Nothing reaches the server,
nothing reaches the destination, and the only trace is a console message
nobody is reading — so a host missing from ``connect-src`` looks exactly like
a host that is there and has nothing to say.
"""

SENTRY_INGESTION = "https://*.sentry.io"


def test_the_base_policy_allows_the_sentry_ingestion_host(settings):
    """The one deployments run on, and the one nothing else exercises.

    The browser suite covers the local policy by making the request for real,
    but it boots Django under local settings and never reads this one, which
    production inherits untouched. A Sentry host added there and not here
    reports nothing from the deploy that matters.

    Asserting the pair together would mean importing ``config.settings.local``,
    which rewrites INSTALLED_APPS underneath a Django that has already booted.
    """
    assert (
        SENTRY_INGESTION
        in settings.CONTENT_SECURITY_POLICY["DIRECTIVES"]["connect-src"]
    )
