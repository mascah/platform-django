AI-Driven Development with Claude Code
=======================================

This guide documents an AI-driven development workflow using `Claude Code <https://claude.ai/code>`_. The approach emphasizes planning, quality gates, and parallel development to ship faster while maintaining code quality.

Why Claude Code for Development
-------------------------------

Claude Code excels at research and planning. Key capabilities:

- **Understanding codebases**: Deep exploration across files and dependencies
- **Research and discovery**: Using tools to investigate problems thoroughly
- **Producing accurate plans**: Detailed implementation strategies
- **Iterative refinement**: Conversations that build understanding over time

This workflow separates **planning and discovery** from **implementation**. By treating these as distinct phases, you gain flexibility: plan on mobile, implement on your laptop, or queue up work for later.

The Planning Workflow
---------------------

Starting a Feature
^^^^^^^^^^^^^^^^^^

Begin with a prompt that describes the problem you're solving. Use **plan mode** for best results::

    claude --plan

In plan mode, Claude will:

1. Explore the codebase to understand existing patterns
2. Research the problem space
3. Draft an implementation plan
4. Iterate based on your feedback

Iterating on Plans
^^^^^^^^^^^^^^^^^^

Plans rarely emerge perfect on the first attempt. Iterate by:

- Asking clarifying questions
- Requesting alternatives
- Adjusting scope
- Adding constraints

Once satisfied, you have two options for preserving the plan:

**Option 1: Write to disk**::

    "Please write this plan to docs/plans/feature-name.md"

**Option 2: Create a GitHub issue**::

    "Please create a GitHub issue for this feature using the gh CLI"

The GitHub issue approach provides a powerful decoupling point---plan from anywhere and implement later.

Quality Gates as AI Guardrails
------------------------------

Pre-commit hooks are the **moat around your software castle**. They ensure AI-generated code meets your standards before it enters the repository.

The Critical Rule
^^^^^^^^^^^^^^^^^

**Never allow Claude to bypass git hooks.** We've configured Claude Code to prevent the ``--no-verify`` flag:

.. code-block:: json

    // .claude/settings.local.json
    {
      "permissions": {
        "deny": [
          "Bash(git commit:*--no-verify*)",
          "Bash(git push:*--no-verify*)"
        ]
      }
    }

Why This Matters
^^^^^^^^^^^^^^^^

When Claude implements a feature and attempts to commit:

1. Pre-commit hooks run (linting, formatting, type checking, tests)
2. If hooks fail, Claude must fix the issues
3. This creates a feedback loop where Claude corrects its own mistakes
4. You spend less time pointing out problems

This is where AI significantly reduces your workload---instead of reviewing and requesting fixes, the hooks enforce standards automatically.

What to Include in Pre-Commit Hooks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Build a fast feedback loop. Every check should run quickly:

- **Linting** --- Ruff for Python, ESLint for JavaScript/TypeScript
- **Formatting** --- Ruff format, Prettier
- **Type checking** --- mypy, TypeScript
- **Fast tests** --- Unit tests, not integration tests
- **Security checks** --- Detect secrets, validate syntax

See :doc:`quality-gates` for the full Lefthook configuration.

The goal: **shippable code by the time pre-commit succeeds**.

Parallel Development with Worktrees
-----------------------------------

The Problem
^^^^^^^^^^^

Running multiple Claude sessions on the same codebase creates conflicts:

- File changes collide
- Git state becomes confused
- Context switches between features become painful

The Solution: Git Worktrees
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Git worktrees allow multiple working directories from a single repository. Each worktree has its own branch and working state, completely isolated from others.

**Creating a new worktree** (with automatic port allocation)::

    # From main worktree
    . bin/worktree-new feature-branch

This script:

- Creates a git worktree at ``../platform-django--feature-branch``
- Auto-generates ``.env.local`` with unique ``DOCKER_HOST_DJANGO_PORT`` and ``VITE_PLATFORM_DJANGO_PORT``
- Copies configuration files (``.env``, ``.npmrc``)
- Runs ``pnpm install``

**Starting development in a worktree**::

    just up           # Start Docker stack (uses worktree-specific ports)
    pnpm dev          # Start Vite (uses worktree-specific port)

**Checking your ports**::

    just ports
    # Output: Django: 8010, Vite: 5183

**Removing a worktree**::

    . bin/worktree-remove

Understanding Serial vs. Parallel Work
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Not all work can be parallelized. Consider:

**Parallel-safe:**

- Independent features
- Bug fixes in unrelated areas
- Documentation updates
- Test additions

**Requires serial work:**

- Changes to shared infrastructure
- Database migrations that conflict
- Core API changes affecting multiple features

GitHub Integration
------------------

Creating Issues with Claude
^^^^^^^^^^^^^^^^^^^^^^^^^^^

When planning produces actionable work::

    "Create a GitHub issue for this feature with the implementation plan"

Claude will use ``gh issue create`` with:

- Clear title
- Problem description
- Implementation steps
- Acceptance criteria

PR Review with Claude Code
^^^^^^^^^^^^^^^^^^^^^^^^^^

Claude Code offers a GitHub Action for automated PR reviews, providing:

- Code review comments
- Suggestions for improvements
- Identification of potential issues

Putting It Together
-------------------

The Complete Workflow
^^^^^^^^^^^^^^^^^^^^^

1. **Plan** --- Start Claude in plan mode, describe the problem
2. **Iterate** --- Refine the plan until it's solid
3. **Capture** --- Create a GitHub issue or save to disk
4. **Isolate** --- Create a worktree for the feature
5. **Implement** --- Point Claude at the issue, let it work
6. **Gate** --- Pre-commit hooks enforce quality
7. **Ship** --- Push branch, create PR, automated review

The Operator Mindset
^^^^^^^^^^^^^^^^^^^^

With this workflow, you become an **operator** orchestrating AI activity:

- Set up strong guarantees (hooks, tests, types)
- Let AI meet those requirements
- Don't tell Claude what's wrong---let the tools tell it
- Focus on architecture and direction

Multiple terminals can run simultaneously:

- 2-3 creating GitHub issues from planning conversations
- 2-3 implementing issues in separate worktrees
- Background: PR reviews running automatically

The bottleneck shifts from "writing code" to "understanding what can be parallelized."

Building Your Moat
^^^^^^^^^^^^^^^^^^

The stronger your quality gates, the more you can trust AI output:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Investment
     - Payoff
   * - Fast test suite
     - Catch bugs before commit
   * - Strict type checking
     - Eliminate type errors automatically
   * - Comprehensive linting
     - Consistent code style, no bike-shedding
   * - Security checks
     - Prevent secrets and vulnerabilities
   * - Pre-commit enforcement
     - AI fixes its own issues

Each investment compounds. A 2-minute pre-commit that catches 80% of issues saves hours of review time across hundreds of commits.

Quick Reference
---------------

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Task
     - Command
   * - Start planning session
     - ``claude --plan``
   * - Create worktree (with port allocation)
     - ``. bin/worktree-new branch-name``
   * - Remove worktree
     - ``. bin/worktree-remove``
   * - Check assigned ports
     - ``just ports``
   * - Start Docker stack
     - ``just up``
   * - Start Vite dev server
     - ``pnpm dev``
   * - Create GitHub issue
     - ``gh issue create --title "..." --body "..."``
   * - Run pre-commit manually
     - ``lefthook run pre-commit``
   * - List worktrees
     - ``git worktree list``
