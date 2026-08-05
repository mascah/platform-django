# Worktrees are created by the agent harness, backed by a script in this repo

Creating a worktree is triggered from inside an agent session rather than from a
shell, because the workflow this template is built around is managing several
agent sessions at once and deciding partway through that one of them needs its
own workspace. A small script in this repository sits behind that trigger:
create the worktree, find free ports for the application processes, generate the
`.env`, start dependency installation without blocking, report the path.

## Considered Options

Shell-first creation would make the hardest part of this — getting per-worktree
values into an agent's shell — cease to exist rather than be solved, since a
process launched from a prepared shell inherits everything. It was rejected on
workflow grounds: it forces a trip out to a terminal and back for every
worktree, which is precisely the friction that caused the previous tooling to be
abandoned.

Two existing tools were considered. Both are capable, and the job had already
shrunk beneath them: once backing services are shared (ADR-0003), allocation is
two ports rather than six, and a central registry of who holds what is better
served by the generated `.env` inside the worktree itself — the record lives in
the thing it describes, so it cannot go stale and there is nothing to clean up.
The remaining argument for a binary was per-command environment injection. That
was briefly a Bash hook, and is now nobody's job: `just` loads `.env` itself and
Django reads it directly (ADR-0002), which covers every command this template
documents.

## Consequences

A copy of this template can create worktrees with nothing installed beyond the
toolchain, which matters because every tool the template *requires* must be
installed on every machine, in every remote environment, for every project.

Two worktrees created in the same instant can probe the same free port. This is
accepted: it surfaces immediately as a bind error, and a lock is the upgrade
path if it ever happens in practice.

A command run outside `just` — a bare `psql`, `pnpm` or `redis-cli` — sees the
ambient environment rather than this worktree's, and so can address the wrong
database quietly. Prefix it with `mise exec --` where that matters. The hook
that used to inject the environment per command was removed rather than fixed:
it had to prefix every command with a command substitution, an agent session
isolated in a worktree refuses to run any command it cannot statically certify
as staying inside that worktree, and a substitution is uncertifiable by
construction. That left such a session able to edit files or run commands but
never both — too sharp an edge for what `just` and Django already cover.
