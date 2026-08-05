"""Cross-cutting request handling that belongs to no single module."""

from collections.abc import Callable

from django.conf import settings
from django.http import HttpRequest
from django.http import HttpResponse

SESSION_HINT_COOKIE = "session_hint"


class SessionHintMiddleware:
    """Keep the session hint in step with the session, and off the cache key.

    The hint is a non-authoritative boolean cookie meaning "somebody is signed
    in here". It exists so a document that is byte-identical for every visitor
    can still pick the right call to action before the first paint, with no
    network round trip. It is never authentication: ``sessionid`` stays
    httpOnly, every protected route keeps checking the session server-side, and
    forging this cookie changes a button label and nothing else.

    Reconciling on the way out, rather than at login, is what makes it
    self-healing. A signal cannot set a cookie — it has no response to write to
    — and hooking allauth alone would miss the Django admin, social login and
    plain session expiry. Every response passes through here, so the hint
    corrects itself on the next request to Django whatever ended the session.

    Ordering matters twice over. It must sit *below* WhiteNoise, so static
    files never reach it, and *above* ``SessionMiddleware`` and
    ``LocaleMiddleware``, because both stamp ``Vary`` in their own
    ``process_response`` and only an outer middleware can take it off again.
    ``request.session`` is still readable from out here: the inner middleware
    attached it on the way in.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)

        session = getattr(request, "session", None)
        # Read the session key rather than request.user: the session is already
        # loaded by this point, and touching request.user would fetch a row we
        # do not need to answer a yes-or-no question.
        signed_in = bool(session and session.get("_auth_user_id"))
        hint = request.COOKIES.get(SESSION_HINT_COOKIE)

        if signed_in and hint != "1":
            response.set_cookie(
                SESSION_HINT_COOKIE,
                "1",
                max_age=settings.SESSION_COOKIE_AGE,
                secure=settings.SESSION_COOKIE_SECURE,
                httponly=False,
                samesite="Lax",
            )
        elif not signed_in and hint is not None:
            response.delete_cookie(SESSION_HINT_COOKIE)

        # A response that calls itself publicly cacheable must not also claim to
        # vary by cookie: the two contradict each other, and a CDN honouring the
        # Vary would key on every visitor's analytics cookie and cache nothing.
        # Session and locale middleware add it to every response indiscriminately
        # — proven on a request carrying no cookies at all — so the correction
        # happens here rather than in the view, which returns too early to undo
        # it.
        cacheable = "public" in response.headers.get("Cache-Control", "")
        if cacheable and response.has_header("Vary"):
            del response.headers["Vary"]

        return response
