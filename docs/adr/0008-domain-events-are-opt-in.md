# The template ships no event bus; domain events are a decision, not a default

A modular monolith is expected to arrive with a domain event bus, and this one
does not. The template ships the criteria for deciding an event is warranted and
a checklist for adopting one safely, and no implementation.

The template previously shipped both: a thirty-one line in-memory bus and three
hundred lines of documentation presenting events as a first-class option, with
`CLAUDE.md` going further and requiring that modules communicate through them.
Nothing published an event and nothing subscribed to one, in the template or in
the project built from it.

## Considered Options

Keeping the bus and correcting the documentation around it was the obvious
option, and it is what the downstream project did. The result is instructive:
four separate skill files there carry a paragraph telling agents not to invent
event flows, not to assert event-bus behaviour in tests, and not to reach for a
`FakeEventBus` that was never supported. That prose exists because the bus was
still present to be found. An unused mechanism sitting in the tree is an
invitation, and the documentation warning against it is read later than the code
is found.

Moving it to `libs/` as an uninstalled package was rejected for the same reason
in a quieter form.

## Consequences

A project that needs events builds one deliberately, against the adoption
checklist in `docs/2-architecture/event-driven.rst`: delivery semantics, handler
registration, idempotency, retry behaviour, focused tests, observability. Those
six were always the hard part; a dictionary of handler lists is an afternoon.
Requiring the bus to be written is what makes the checklist unavoidable rather
than aspirational.

Direct downward calls — a higher module calling a lower module's service for a
write or selector for a read — are the established pattern, not a compromise
pending some later event-driven architecture.

The accepted cost is that a project which genuinely wants events writes its own,
and two projects may write slightly different ones. That is cheaper than every
project inheriting one nobody uses.
