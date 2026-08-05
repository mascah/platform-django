"""Cross-cutting request handling that belongs to no single module."""

from collections.abc import Callable

from django.conf import settings
from django.http import HttpRequest
from django.http import HttpResponse

SESSION_HINT_COOKIE = "session_hint"


class SessionHintMiddleware:
    """Keep the session hint in step with the session.

    The hint is a non-authoritative boolean cookie meaning "somebody is signed
    in here". It exists so the landing page — one document, identical for every
    visitor — can still pick the right call to action before the first paint,
    with no network round trip. It is never authentication: ``sessionid`` stays
    httpOnly, every protected route keeps checking the session server-side, and
    forging this cookie changes a button label and nothing else.

    Reconciling on the way out, rather than at login, is what makes it
    self-healing. A signal cannot set a cookie — it has no response to write to
    — and hooking allauth alone would miss the Django admin, social login and
    plain session expiry. Every response passes through here, so the hint
    corrects itself on the next request to Django whatever ended the session.
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

        return response
