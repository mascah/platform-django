# Cross-module foreign keys need a justification, not a prohibition

A foreign key between modules is allowed when a stated reason of a particular
kind supports it: referential integrity or ownership that belongs in the
database, lifecycle coupling tight enough that an integer identifier would lose
a guarantee the project needs, or reverse traversal that is actually used.
Absent such a reason, a module refers to another module's rows by integer
identifier. Where a foreign key is justified but nothing traverses it backwards,
it is declared `related_name="+"`.

The template previously prohibited them outright. That rule had never been
exercised against real code — the template contains no foreign key at all — and
it fails on contact. The first model a project writes will want to record who
owns a row, which in Django is `ForeignKey(settings.AUTH_USER_MODEL)`. Users is
a module and the new domain is a module, so the most standard line in the
framework was forbidden, and forbidden in favour of a bare integer column that
gives up referential integrity, cascade behaviour and `select_related` on
precisely the relation that most wants them.

## Considered Options

The downstream project resolved this as case-by-case judgement, which is right
for a codebase with years of relations to reason from and wrong for one with
none. A project on its first week has no cases; told to judge case by case, an
agent will decide by coin flip and call it judgement. The named reasons are what
make the decision reproducible, and they are what the downstream project's own
review scenarios actually supply when they expect a foreign key to pass review.

The list is illustrative rather than closed. What is required is a stated reason
of this kind, not one of these three verbatim.

## Consequences

The bias still favours integer identifiers, which is what keeps a later split of
a module from becoming a schema migration. The exception exists so that the
common case — a row owned by a user — is written the way Django writes it.

`related_name="+"` on an unused reverse relation is the part most easily
forgotten and the part that does the work: it keeps a justified foreign key from
quietly becoming a two-way dependency through the reverse accessor.
