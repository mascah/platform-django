---
name: github-issues
description: Establish GitHub's native sub-issue relationship between a parent and child issue via `gh`, alongside the human-readable Parent reference in the sub-issue's body. Use when creating a GitHub issue that should be a sub-issue of an existing one, when an existing issue should be linked as a sub-issue of a parent, or when to-tickets publishes tickets under a parent spec issue on GitHub.
---
# GitHub Tickets

GitHub track two independent things, both mean "issue belong to that one" — set only one, sub-issue stay half-linked:

- **Native sub-issue relationship** — GraphQL-backed link, drives parent's progress checklist in GitHub UI, shows in `gh api repos/<owner>/<repo>/issues/<PARENT>/sub_issues`. Nothing in issue body encode it; invisible to anyone reading raw markdown or diff.
- **Parent reference** — `## Parent` section in sub-issue's body (see to-tickets' `issue-template`), plain link/number human or agent find by reading issue, but GitHub's sub-issue API and UI never look at.

Set both, every time. Neither substitute other.

## Creating a new sub-issue

```
gh issue create --repo <owner>/<repo> --title "<title>" --body "<body-with-##-Parent-section>" --parent <PARENT-NUMBER-OR-URL>
```

`--parent` set native relationship at creation time. `--body` must still carry own `## Parent` section — `--parent` no write one for you.

## Linking an existing issue as a sub-issue

```
gh issue edit <PARENT-NUMBER-OR-URL> --repo <owner>/<repo> --add-sub-issue <SUB-NUMBER-OR-URL>
```

One issue per call — loop for multiple sub-issues. Sub-issue's body lack `## Parent` section? Add separately (`gh issue edit <SUB> --body "..."`).

Repeat call error `Issue may not contain duplicate sub-issues` — link already exist, not call failed. Treat as success, move on.

## Verify

```
gh api repos/<owner>/<repo>/issues/<PARENT>/sub_issues -q '.[].number'
```

Sub-issue's number must appear here. `## Parent` section in body not enough confirm native link — check API.
