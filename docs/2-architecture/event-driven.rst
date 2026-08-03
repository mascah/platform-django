Domain Events
=============

The template ships no event bus. Domain events are a decision a project makes
deliberately, not a default it inherits --- see
:doc:`ADR-0008 </adr/0008-domain-events-are-opt-in>`.

The established pattern for cross-module communication is a **direct downward
call**: a higher-level module calls a lower-level module's service for a write,
or its selector for a read. That is not an interim compromise pending some later
event-driven architecture. It is explicit, traceable and typed, and it is what
:doc:`module-dependencies` describes.

When Events Are Worth Considering
---------------------------------

A direct call stops being enough at one of three boundaries:

**Reverse.** A lower-level module needs to notify a higher-level one. A direct
call would invert the dependency direction and create a cycle. This is the
strongest case for events, because the alternative is a design the import
contracts reject.

**Lateral.** Two modules at the same level need to react to each other. Neither
owns the other, so a direct call in either direction imposes an ordering the
domain does not have.

**Multi-consumer.** Three or more modules react to the same occurrence, and the
set is expected to grow. The publishing module otherwise accumulates one call
per consumer, and each new reaction edits code that has nothing to do with it.

Two consumers is not yet a multi-consumer boundary. Two direct calls are cheaper
to read than a bus; the third consumer is where that stops being true.

The Adoption Checklist
----------------------

A dictionary of handler lists is an afternoon's work. These six are the part
that is actually hard, and each must be answered *before* any code is written.

1. **Delivery semantics.** At-most-once, at-least-once or exactly-once? What
   happens to an event whose handler raises? In-process dispatch after commit is
   at-most-once, and losing an event when a handler crashes is the accepted
   cost --- state that, or choose a transport without that property.

2. **Handler registration.** Where are subscriptions declared, and when do they
   run? Registration hidden in import side effects makes the set of handlers for
   an event undiscoverable, which is the failure mode that makes event systems
   hard to reason about.

3. **Idempotency.** Any guarantee above at-most-once means a handler will run
   twice. Each handler is either naturally idempotent or carries a
   deduplication key. Decide per handler, not once for the system.

4. **Retry behaviour.** What retries --- the dispatch, the handler, neither?
   With what backoff and what ceiling? Where does an event go once retries are
   exhausted, and who looks at it there?

5. **Focused tests.** How is "this service published that event" asserted
   without asserting the whole downstream chain, and how is a handler tested
   without publishing? Events are published inside ``transaction.on_commit()``
   callbacks, so a test that does not capture those callbacks silently asserts
   nothing.

6. **Observability.** "Was this event published, and did its handlers run?" must
   be answerable from logs or traces alone. An event system without that is a
   set of side effects with no audit trail.

The Publishing Rule
-------------------

If a project does adopt events, one rule survives from every implementation of
this that has gone wrong: **publish inside** ``transaction.on_commit()``, never
before. An event published before commit is an event whose handlers may process
data that was then rolled back.

See Also
--------

- :doc:`ADR-0008 </adr/0008-domain-events-are-opt-in>` --- why no bus ships
- :doc:`module-dependencies` --- dependency direction and direct-call patterns
- :doc:`service-layer` --- services and selectors, what a downward call reaches
