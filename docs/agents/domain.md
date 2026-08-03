# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

**Layout: single-context.** One `CONTEXT.md` at the repo root plus `docs/adr/`, covering the whole repo — Django modules, `libs/`, `apps/`, and `packages/` share one domain vocabulary. If a package ever grows a genuinely distinct language, split it out then by adding a root `CONTEXT-MAP.md`.

## Before exploring, read these

- **`CONTEXT.md`** at the repo root — the glossary / ubiquitous language.
- **`docs/adr/`** — read ADRs that touch the area you're about to work in.

If any of these files don't exist, **proceed silently**. Don't flag their absence; don't suggest creating them upfront. The `/domain-modeling` skill (reached via `/grill-with-docs` and `/improve-codebase-architecture`) creates them lazily when terms or decisions actually get resolved.

## File structure

```
/
├── CONTEXT.md
├── docs/adr/
│   ├── 0001-no-foreign-keys-between-modules.md
│   └── 0002-domain-events-on-commit.md
├── platform_django/        ← Django modules
├── libs/                   ← isolated, Django-free Python packages
├── apps/                   ← React SPAs
└── packages/               ← shared frontend packages
```

## Numbering a new ADR

The template numbers its ADRs from `0001`. **A downstream project numbers its own from `1001`** — the first one it writes is `docs/adr/1001-<slug>.md`.

The band exists because a project and the template both reaching for the next free number produce two different filenames, both additions, which git merges without a conflict — leaving two ADRs with the same number and every cross-reference to them ambiguous. Reserving a range costs nothing and needs no coordination.

If you are working in the template itself, use the next number in the `00xx` sequence. If `docs/adr/` already contains `1001`-and-up files, you are in a downstream project. See `docs/1-getting-started/staying-connected.rst`.

## Use the glossary's vocabulary

When your output names a domain concept (in an issue title, a refactor proposal, a hypothesis, a test name), use the term as defined in `CONTEXT.md`. Don't drift to synonyms the glossary explicitly avoids.

If the concept you need isn't in the glossary yet, that's a signal — either you're inventing language the project doesn't use (reconsider) or there's a real gap (note it for `/domain-modeling`).

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently overriding:

> _Contradicts ADR-0007 (event-sourced orders) — but worth reopening because…_
