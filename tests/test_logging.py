"""Assertions about what actually comes out of a log handler.

These build the formatter from ``settings.LOGGING`` and read the rendered
bytes, rather than capturing structlog events before rendering. Everything
worth breaking here — the middleware being installed, the processor chain
being applied, ``foreign_pre_chain`` reaching stdlib records — only shows up
once something has been rendered.
"""

import io
import json
import logging
from http import HTTPStatus

from django.conf import settings


def render_through(formatter_name):
    """Attach a handler using one of the configured formatters to the root.

    Returns the stream it writes to and a callable that parses what landed.
    """
    spec = dict(settings.LOGGING["formatters"][formatter_name])
    formatter = spec.pop("()")(**spec)

    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(formatter)
    return handler, stream


def json_lines(stream):
    return [json.loads(line) for line in stream.getvalue().splitlines() if line.strip()]


def test_a_request_is_logged_as_json_carrying_its_request_id(client, db):
    """The whole point of the middleware: correlate every line of one request."""
    handler, stream = render_through("json")
    root = logging.getLogger()
    root.addHandler(handler)
    try:
        response = client.get("/healthz/")
    finally:
        root.removeHandler(handler)

    assert response.status_code == HTTPStatus.OK

    events = {entry["event"]: entry for entry in json_lines(stream)}
    assert "request_started" in events, events
    assert "request_finished" in events, events

    # Bound by the middleware into a contextvar, merged back in by
    # `merge_contextvars`. Absent if the middleware is not first, or if the
    # processor list loses that entry.
    request_id = events["request_started"]["request_id"]
    assert request_id
    assert events["request_finished"]["request_id"] == request_id


def test_a_stdlib_log_is_rendered_by_the_same_chain():
    """`foreign_pre_chain` is what makes a third-party log match ours.

    A package that knows nothing about structlog still comes out with a level,
    a logger name and a timestamp, in the same JSON shape.
    """
    handler, stream = render_through("json")
    logger = logging.getLogger("some.third.party.package")
    logger.addHandler(handler)
    logger.propagate = False
    try:
        logger.warning("plain stdlib call")
    finally:
        logger.removeHandler(handler)
        logger.propagate = True

    (entry,) = json_lines(stream)
    assert entry["event"] == "plain stdlib call"
    assert entry["level"] == "warning"
    assert entry["logger"] == "some.third.party.package"
    assert entry["timestamp"]
