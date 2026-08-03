# Backing services are shared per machine; worktrees isolate logically

One Postgres and one Redis serve every worktree on a machine. A worktree gets
its own database and its own Redis logical database rather than its own
containers, so only the application processes need a port allocated to them.

## Considered Options

A full stack per worktree was the previous arrangement. It gave each worktree
isolation of the *Postgres version*, which matters during an upgrade and
essentially never during feature work, and charged for it continuously: at the
five to seven worktrees this template is meant to support, that is a dozen-odd
containers and six offset ports each. The isolation that actually matters
between worktrees is of schema and data, which a separate database provides
completely — the test runner already creates its own databases per run, so
running tests in parallel is unaffected.

## Consequences

Cross-project port pressure mostly disappears with the per-project port offset
that existed only to keep each project's own Postgres and Redis apart, which in
turn removes most of what made worktree management cumbersome.

Two costs are accepted deliberately. Destroying all backing-service data becomes
a machine-wide action rather than a per-worktree one, so tearing down a worktree
means dropping its database rather than removing its containers. And upgrading
Postgres becomes a coordinated change across worktrees rather than something a
single branch can do alone; a private stack for that case can be added if it is
ever actually needed.
