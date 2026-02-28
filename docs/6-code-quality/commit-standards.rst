Commit Standards
================

This guide documents Git workflow and commit conventions for the project.

Commit Messages
---------------

Format
^^^^^^

Follow the conventional commit format::

    <type>(<scope>): <subject>

    <body>

    <footer>

**Type** (required):

- ``feat``: New feature
- ``fix``: Bug fix
- ``docs``: Documentation changes
- ``style``: Formatting, no code change
- ``refactor``: Code restructuring without behavior change
- ``test``: Adding or updating tests
- ``chore``: Maintenance tasks

**Scope** (optional): Module or area affected (e.g., ``users``, ``api``, ``ui``)

**Subject** (required): Short description in imperative mood

Examples
^^^^^^^^

Good commit messages::

    feat(users): add email verification flow

    fix(orders): handle null shipping address

    docs: update authentication guide

    refactor(api): extract pagination logic to base class

    test(orders): add integration tests for checkout

Bad commit messages::

    fixed stuff
    WIP
    updates
    asdf

Branch Naming
-------------

Use descriptive branch names with prefixes::

    feat/user-authentication
    fix/order-calculation-bug
    docs/api-documentation
    refactor/service-layer

For issue tracking integration::

    feat/PROJ-123-user-authentication
    fix/PROJ-456-order-bug

Pull Request Workflow
---------------------

Creating PRs
^^^^^^^^^^^^

1. **Create a feature branch** from ``main``::

    git checkout main
    git pull
    git checkout -b feat/new-feature

2. **Make commits** following commit message conventions

3. **Push and create PR**::

    git push -u origin feat/new-feature
    gh pr create --title "feat: add new feature" --body "..."

PR Description Template
^^^^^^^^^^^^^^^^^^^^^^^

Include in your PR description::

    ## Summary
    Brief description of what this PR does.

    ## Changes
    - List of specific changes
    - Another change

    ## Testing
    How to test these changes:
    1. Step one
    2. Step two

    ## Screenshots (if applicable)
    Visual changes shown here.

Review Process
^^^^^^^^^^^^^^

1. PRs require at least one approval
2. All CI checks must pass
3. Resolve all review comments
4. Squash merge to main (default)

Pre-commit Hooks
----------------

Lefthook runs automatically on commit. Hooks include:

- **Linting**: Ruff, ESLint
- **Formatting**: Ruff format, Prettier
- **Type checking**: mypy, TypeScript
- **Tests**: Fast unit tests
- **Security**: Secret detection

If hooks fail, fix the issues and commit again. Never bypass hooks with ``--no-verify`` --- in rare cases where it's genuinely necessary (production hotfixes, broken tooling), see :doc:`/5-ai-development/quality-gates` for guidance.

See :doc:`linting-formatting` for hook configuration details.

Git Best Practices
------------------

Keeping History Clean
^^^^^^^^^^^^^^^^^^^^^

- **Rebase feature branches** before merging::

    git fetch origin
    git rebase origin/main

- **Squash WIP commits** into logical units::

    git rebase -i HEAD~3

- **Write meaningful commits** --- each commit should be a logical unit

Handling Conflicts
^^^^^^^^^^^^^^^^^^

1. Fetch latest main::

    git fetch origin

2. Rebase your branch::

    git rebase origin/main

3. Resolve conflicts file by file

4. Continue rebase::

    git add .
    git rebase --continue

5. Force push (only on feature branches)::

    git push --force-with-lease

Protected Branches
------------------

The ``main`` branch is protected:

- Direct pushes are blocked
- PRs require passing CI
- PRs require at least one approval
- Branch must be up to date before merging

Release Process
---------------

The project follows a deployment workflow:

1. Merge PR to ``main``
2. CI builds and tests
3. Deployment to staging
4. Promotion to production (if applicable)

Tagging Releases
^^^^^^^^^^^^^^^^

For versioned releases::

    git tag -a v1.2.3 -m "Release v1.2.3"
    git push origin v1.2.3

See Also
--------

- :doc:`linting-formatting` --- Code quality tools
- :doc:`/5-ai-development/claude-code-workflow` --- AI-assisted development workflow
