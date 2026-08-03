Quality Gates for AI Development
=================================

Pre-commit hooks serve as quality gates that ensure AI-generated code meets standards. This guide documents the Lefthook configuration and how it supports AI-assisted development.

Why Quality Gates Matter
------------------------

When AI assistants like Claude Code write code:

1. They may not know your project's specific conventions
2. They might introduce subtle type errors
3. Formatting may not match your standards
4. Security issues could slip through

Quality gates catch these issues **before code enters the repository**. The AI gets immediate feedback and fixes problems automatically.

Lefthook Configuration
----------------------

The project uses Lefthook for pre-commit hooks. Configuration is in ``lefthook.yml``:

.. code-block:: yaml

    pre-commit:
      parallel: true
      commands:
        # === File validation ===
        trailing-whitespace:
          glob: '*.{py,ts,tsx,js,jsx,json,yaml,yml,toml,md,html,css}'
          run: |
            for file in {staged_files}; do
              sed -i '' 's/[[:space:]]*$//' "$file"
            done
          stage_fixed: true

        check-json:
          glob: '*.json'
          run: python3 -c "import json, sys; [json.load(open(f)) for f in sys.argv[1:]]" {staged_files}

        detect-private-key:
          run: "! grep -rn 'PRIVATE KEY-----' {staged_files}"

        # === Python formatting ===
        ruff-check:
          glob: '*.py'
          exclude: '^docs/|/migrations/'
          run: uv run ruff check --force-exclude --fix --exit-non-zero-on-fix {staged_files}
          stage_fixed: true

        ruff-format:
          glob: '*.py'
          exclude: '^docs/|/migrations/'
          run: uv run ruff format --force-exclude {staged_files}
          stage_fixed: true

        # === Python type checking ===
        mypy:
          glob: '*.py'
          exclude: '^docs/|/migrations/'
          run: uv run mypy . --config-file=pyproject.toml

        # === Architectural enforcement ===
        import-linter:
          glob: '*.py'
          exclude: '^docs/|/migrations/'
          run: uv run lint-imports

        # === Documentation build ===
        docs-build:
          glob: 'docs/**/*'
          run: uv run sphinx-build -W -q docs docs/_build/html

        # === Frontend ===
        turbo-typecheck:
          glob: '*.{ts,tsx}'
          run: pnpm turbo typecheck

        turbo-lint:
          glob: '*.{ts,tsx,js,jsx}'
          run: pnpm turbo lint

        prettier:
          glob: '*.{ts,tsx,js,jsx,json,css,md}'
          run: pnpm format
          stage_fixed: true

Hook Categories
---------------

File Validation
^^^^^^^^^^^^^^^

Basic file hygiene:

- **trailing-whitespace**: Removes trailing whitespace
- **end-of-file-fixer**: Ensures files end with newline
- **check-json**: Validates JSON syntax
- **check-yaml**: Validates YAML syntax
- **detect-private-key**: Blocks commits containing private keys

Python Quality
^^^^^^^^^^^^^^

- **ruff-check**: Linting with auto-fix for import sorting, unused imports
- **ruff-format**: Code formatting (Black-compatible)
- **mypy**: Static type checking
- **django-upgrade**: Modernizes Django code patterns

Architectural Enforcement
^^^^^^^^^^^^^^^^^^^^^^^^^

- **import-linter**: Enforces module boundaries
- **docs-build**: Ensures documentation builds without warnings

Frontend Quality
^^^^^^^^^^^^^^^^

- **turbo-typecheck**: TypeScript type checking
- **turbo-lint**: ESLint for JavaScript/TypeScript
- **prettier**: Code formatting

The AI Feedback Loop
--------------------

When Claude Code attempts to commit:

1. **Hooks run** on staged files
2. **Auto-fixes apply** (formatting, import sorting)
3. **Errors surface** for issues requiring manual fix
4. **Claude sees the error** and corrects the code
5. **Commit succeeds** when all hooks pass

This creates a virtuous cycle where AI learns from immediate feedback.

Example: Type Error Caught
^^^^^^^^^^^^^^^^^^^^^^^^^^

Claude writes code with a type error:

.. code-block:: python

    def get_user(user_id: str) -> User:  # Bug: should be int
        return User.objects.get(id=user_id)

mypy catches this::

    error: Argument 1 to "get" has incompatible type "str"; expected "int"

Claude fixes it:

.. code-block:: python

    def get_user(user_id: int) -> User:
        return User.objects.get(id=user_id)

Example: Import Boundary Violated
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Claude imports across module boundaries:

.. code-block:: python

    # In platform_django/billing/services.py
    from platform_django.orders.models import Order  # Violation!

import-linter catches this::

    orders cannot import from billing (independence contract violated)

Claude fixes it by calling ``orders``' selector for a DTO, or by moving the behaviour into the higher-level module.

Preventing Hook Bypass
----------------------

AI assistants might try to bypass hooks with ``--no-verify``. Block this:

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

This ensures Claude **cannot skip quality gates**.

Optimizing Hook Performance
---------------------------

Fast hooks encourage use. Optimize for speed:

**Parallel execution**:

.. code-block:: yaml

    pre-commit:
      parallel: true

**Targeted file globs**:

.. code-block:: yaml

    ruff-check:
      glob: '*.py'
      exclude: '^docs/|/migrations/'

**Only staged files**:

.. code-block:: yaml

    run: uv run ruff check {staged_files}

**Skip slow tests**:

Run unit tests in hooks, integration tests in CI.

Running Hooks Manually
----------------------

Run all hooks::

    lefthook run pre-commit

Run a specific hook::

    lefthook run pre-commit --commands mypy

Skip hooks (for emergencies only)::

    git commit --no-verify  # Blocked for AI assistants

Adding New Hooks
----------------

Add a new check to ``lefthook.yml``:

.. code-block:: yaml

    pre-commit:
      commands:
        new-check:
          glob: '*.py'
          run: uv run my-new-checker {staged_files}
          stage_fixed: true  # If it auto-fixes

Ensure new hooks are:

1. **Fast** --- Under 10 seconds for most changes
2. **Deterministic** --- Same input produces same output
3. **Informative** --- Clear error messages

Troubleshooting
---------------

When Hooks Legitimately Need Bypass
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There are rare cases where bypassing hooks is appropriate:

**Production hotfixes**: When a critical bug is in production and every minute counts, skip hooks
to deploy the fix, then follow up with a proper PR that passes all checks.

**Tooling is broken**: If a hook is failing due to a bug in the tool itself (not your code),
temporarily skip while you fix the tool configuration.

**Migrations or generated files**: Auto-generated files may not pass linters. Add them to the
exclude patterns in ``lefthook.yml`` rather than skipping the entire hook.

**How humans can bypass** (for emergencies)::

    git commit --no-verify -m "HOTFIX: critical production fix - hooks will pass in follow-up PR"

**AI assistants cannot bypass**. The permission configuration blocks Claude Code from using
``--no-verify``. If Claude encounters a hook failure it cannot fix, it should:

1. Report the error to the user
2. Ask for guidance
3. Not attempt workarounds

Hook Failures Claude Can't Fix
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Some hook failures require human intervention:

- **Security issues** (``detect-private-key``): Claude should never have access to real secrets
- **Architectural violations** (``import-linter``): May require design discussion
- **External dependencies** (``turbo typecheck`` failures in other packages): May need separate PR

When Claude encounters these, it should explain the issue and suggest next steps rather than
repeatedly trying different approaches.

False Positives
^^^^^^^^^^^^^^^

If a hook reports an error that isn't actually a problem:

1. **Check if the rule makes sense**: Maybe the rule is right and the code needs fixing
2. **Add a targeted ignore**: Use ``# noqa: RULE`` (Ruff) or ``// eslint-disable-next-line rule-name``
3. **Update the configuration**: If the rule doesn't apply to your project, disable it globally
4. **Report upstream**: If the tool has a bug, file an issue

.. note::

   Add ignores sparingly. Each ignore is technical debt. If you find yourself adding many ignores
   for the same rule, reconsider whether the rule should be disabled globally.

See Also
--------

- :doc:`/6-code-quality/linting-formatting` --- Detailed linting configuration
- :doc:`/6-code-quality/type-checking` --- Type checking setup
- :doc:`/2-architecture/module-boundaries` --- Import-linter contracts
- :doc:`claude-code-workflow` --- AI development workflow
