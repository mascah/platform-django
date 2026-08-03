# Connection URLs are composed in settings, from primitives in one generated `.env`

Each environment gets exactly one generated `.env` holding primitive values —
credentials, hosts, ports, the worktree ID — and Django composes `DATABASE_URL`
and `REDIS_URL` from those primitives itself, falling back to the URL variables
when they are already set by a platform that supplies them. Nothing outside the
repo needs to run for a fresh checkout to boot.

## Considered Options

Deriving the URLs in a shell hook was the previous arrangement, and it made a
shell hook load-bearing for correctness: the URLs only existed inside a shell
that had been hooked, so a container started from the same `.env` could not
resolve them, and a remote environment could not either. Having the worktree
creation step write fully-resolved URLs instead would have been correct
everywhere, but it makes the repository unable to run without whatever tool
generated the file.

## Consequences

The URL variables remain the override, so platforms that inject one directly
keep working untouched. A second dotenv file layered on top of the first was
rejected along with this: merging happens once, visibly, when the file is
generated, rather than at read time in each of the four tools that read it.
