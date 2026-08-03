---
name: cross-module-dependencies
description: Use when changing or reviewing code that crosses a module boundary under platform_django/, or when deciding dependency direction, DTO boundaries, cross-module foreign keys, Celery dispatch, or whether a case justifies domain events.
---

# Cross-Module Dependencies

Start in the code, not the diagram. Inspect the caller, the callee's public
service or selector entrypoint, the current callers of that entrypoint, and
`.importlinter`. Current code and the contracts beat stale prose.

## Decision workflow

**1. Identify direction and ownership.**

A higher-level module may call a lower-level one directly. Direct downward calls
are valid — they are the established pattern, not an interim compromise. Use the
callee's public selector for a read and its service for a write, and reuse the
existing exported function and caller contract before inventing a wrapper.

Prefer `entity_action` names for new public services and selectors. Prefer
keyword-only parameters when a new public operation has two or more inputs.
Treat these as consistency guidance, not findings without a concrete
readability, compatibility, or misuse risk.

**2. If the need is request/response, prefer a direct call.**

New cross-module APIs return primitives or a small stable DTO, not ORM models or
querysets, so that one module does not come to depend on another's field list.
If an existing public API leaks an ORM model, treat that as a migration
constraint: preserve it where current callers require it, and do not broaden it.
Do not add a mediator to hide one valid import.

**3. If the work is asynchronous or external, keep it explicit.**

Perform the state change in the owning service, then queue Celery from
`transaction.on_commit(...)`. Snapshot IDs or other primitives before the
callback rather than closing over a mutable ORM instance.

**4. If the direction is upward or lateral, do not force the import.**

The contracts reject it, and they are right to. Resolve in this order: move the
behaviour up to the module that owns the reaction; extract a lower-level module
both can depend on; only then consider events.

**5. Consider events only for reverse, lateral, or multi-consumer boundaries.**

The template ships no event bus, and no runtime supports one. Adopting events
means answering the six-item checklist in
`docs/2-architecture/event-driven.rst` first — delivery semantics, handler
registration, idempotency, retry behavior, focused tests, observability. Do not
write code against a bus that does not exist.

**6. Decide cross-module foreign keys case by case.**

There is no blanket "integer IDs only" rule. A foreign key across a boundary
needs a stated justification of a named kind: ownership or referential integrity
best enforced in the database, lifecycle coupling an integer identifier would
weaken, or reverse traversal actually in use. The list is illustrative, not
closed. Absent such a reason, refer by integer identifier; where a justified
relation is never traversed backwards, use `related_name="+"`.

## Verification

Run the smallest checks that cover the boundary change:

- `uv run lint-imports`
- focused `pytest` for the touched caller and callee modules
- `git diff --check`

`.importlinter` is a partial gate. It proves declared directions and internal
layers. It does not prove that a cross-module call returns a DTO, that a side
effect is scheduled after commit, or that a foreign key carries a justification
— those stay review concerns.

## References

- `docs/2-architecture/module-dependencies.rst` — module levels and the call
  patterns
- `docs/2-architecture/module-boundaries.rst` — what the contracts prove
- `docs/2-architecture/event-driven.rst` — the events decision and its checklist
- `docs/adr/0008-domain-events-are-opt-in.md`,
  `docs/adr/0009-cross-module-foreign-keys-by-justification.md`
- `.importlinter`
- `platform_django/users/services.py` and `selectors.py` — the public entrypoint
  shape a caller uses
