# platform-django

A modular-monolith Django backend with a Turborepo React frontend, built to be
copied. A project made from this template is a clone plus `PROJECT_SLUG` and
`PROJECT_DISPLAY_NAME` — nothing the template ships gets renamed, so changes
merge in both directions (ADR-0006).

## Authority

Four levels, in descending authority:

1. **Executable checks** — `pytest`, `ruff`, `mypy`, `lint-imports`, `lefthook`, `sphinx -W`
2. **Scoped agent instructions** — the nearest `CLAUDE.md` to the file you are editing
3. **Skills** — `.claude/skills/`, routed below
4. **Documentation** — `docs/`, `CONTEXT.md`, `docs/adr/`

Current code and executable configuration outrank prose when the two disagree.
Read the module you are changing, its callers and its nearby tests before
applying any documented pattern.

`platform_django/users/` is the worked example. Its service, selector, viewset
and tests are what "match the surrounding code" resolves to.

## Stable invariants

- Writes live in `services.py`, reads in `selectors.py`. Views, serializers and
  tasks delegate to them; they do not reimplement a mutation or a scoped query.
- Cross-module calls go downward: a higher module calls a lower module's service
  for a write or its selector for a read. Direct downward calls are valid — the
  established pattern, not an interim compromise.
- Cross-module returns are primitives or stable DTOs, never ORM models.
- Cross-module foreign keys need a stated justification: database-enforced
  integrity or ownership, lifecycle coupling an integer identifier would weaken,
  or reverse traversal actually in use. Otherwise refer by integer identifier,
  and where nothing traverses backwards, `related_name="+"` (ADR-0009).
- The template ships no event bus. Events are a decision answered against the
  six-item checklist in `docs/2-architecture/event-driven.rst` (ADR-0008).
- Side effects that must not survive a rollback are scheduled from
  `transaction.on_commit()`, capturing primitives rather than ORM instances.
- `libs/` packages stay Django-free and `platform_django`-free, configured by
  injection rather than by reading settings.
- Never `--no-verify`. It is blocked, and the hooks are the first authority
  level.
- No secrets in code; configuration arrives through the environment.

## Skill routing

| Task or path                                                                | Skill                       |
| --------------------------------------------------------------------------- | --------------------------- |
| Model fields, constraints, validation, properties, relations                | `django-model`              |
| Business writes, transactions, post-commit side effects                     | `django-service`            |
| Read paths, query functions, eager loading, access scoping                  | `django-selector`           |
| DRF endpoints, serializers, viewsets, routes, OpenAPI annotations           | `django-api`                |
| Celery tasks, retries, scheduling, transaction-safe dispatch                | `django-celery`             |
| pytest coverage for any Django layer                                        | `django-test`               |
| Implementing anything — classify the change and write its tests with it     | `add-tests`                 |
| Crossing a module boundary; dependency direction, DTOs, the events question | `cross-module-dependencies` |
| A new module under `platform_django/`                                       | `new-django-module`         |
| A new stateless Django-free package under `libs/`                           | `new-python-lib`            |
| Django API changes that reach the generated TypeScript client               | `openapi-client`            |
| Mounting or serving a Vite app from Django; templates, CSP, static assets   | `vite-django`               |
| Issues, labels and the `gh` workflow                                        | `github-issues`             |
| Driving a browser for e2e work                                              | `playwright-cli`            |

Skills are mirrored to `.agents/` and `.cursor/` by `bin/sync-agents`. Edit the
copy under `.claude/skills/`; CI fails on a stale mirror.

## Verify

| Area                           | Commands                                                |
| ------------------------------ | ------------------------------------------------------- |
| Python                         | `uv run pytest`, `uv run ruff check .`, `uv run mypy .` |
| Architecture                   | `uv run lint-imports`                                   |
| Isolated libs                  | `just libs-test`, `just libs-test-one <name>`           |
| Frontend                       | `pnpm lint`, `pnpm typecheck`, `pnpm build`             |
| End-to-end                     | `pnpm test:e2e`                                         |
| Docs                           | `just docs`                                             |
| Everything CI runs on a commit | `lefthook run pre-commit --all-files`                   |

Run the narrowest check that covers the change first, then widen.

## Commands worth knowing

`just --list` is the catalogue. These are the ones that go wrong when guessed:

- `just ports` — this worktree's ports, database and Redis index. Django is not
  always on 8000, and the OpenAPI generator's config assumes it is.
- `just up` — start the shared backing services and create _this_ worktree's
  database. `just down` and `just prune` act on containers shared by every
  worktree and every project on the machine.
- `just serve` and `pnpm dev` — Django and Vite, on this worktree's ports.
- `just manage <cmd>` — `manage.py` against this worktree's database.

Worktree creation, isolation and teardown are in the README and ADR-0003/0004.

## Repository conventions

- Issues live as GitHub issues in `mascah/platform-django`, managed with `gh` —
  `docs/agents/issue-tracker.md`.
- Five canonical triage labels, each string equal to its name —
  `docs/agents/triage-labels.md`.
- One `CONTEXT.md` plus `docs/adr/` are the whole domain context, written
  lazily as terms and decisions get resolved — `docs/agents/domain.md`.
- `bin/eject` is the one-way exit for a project that has outgrown the template
  (ADR-0007).
