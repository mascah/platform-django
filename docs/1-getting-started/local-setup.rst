Local Development Setup
=======================

Setting up the development environment.

Quick Start
-----------

**Prerequisites**: Docker Desktop, for the backing services.

**Bootstrap** (one command makes the checkout runnable — installs the pinned
toolchain, both dependency sets, and the environment file). It assumes no
package manager and works on macOS and Linux, as any user::

    bin/bootstrap

**Setup** (optional, macOS) adds developer conveniences on top — shell
integration so commands work without a ``mise exec`` prefix, and git hooks::

    just setup

Then start the Docker stack and Vite dev server::

    just up
    pnpm dev

Access the app at http://localhost:8000/app/

Verify your setup:

1. **Django admin**: http://localhost:8000/admin/ --- login page loads
2. **API schema**: http://localhost:8000/api/schema/ --- JSON response
3. **Frontend**: http://localhost:8000/app/ --- React app loads

Development Workflow
--------------------

1. **Start Docker stack** (Django, PostgreSQL, Redis, Celery)::

       just up

   This starts all services in ``docker-compose.yml``.

2. **Start Vite dev server** (runs on host for HMR)::

       pnpm dev

3. **View logs**::

       just logs

4. **Run management commands**::

       just manage migrate
       just manage createsuperuser

.. _common-commands:

Common Commands
---------------

Backend (Django)
^^^^^^^^^^^^^^^^

.. code-block:: bash

    # Shared backing services (Postgres, Redis, Mailpit)
    just up                   # Start them, and create this worktree's database
    just down                 # Stop them (affects every worktree)
    just logs                 # View their logs
    just psql                 # Open psql on this worktree's database

    # Application processes (run on the host)
    just serve                # Run Django on this worktree's port
    just worker               # Run a Celery worker

    # Management
    just manage migrate       # Run migrations
    just manage createsuperuser  # Create admin user

    # Quality
    pytest                    # Run tests
    just libs-test            # Run tests for all isolated Python packages
    just libs-test-one <name> # Run tests for a specific lib
    just coverage             # Run tests with coverage
    just coverage-check       # Check minimum 85% threshold
    mypy platform_django      # Type checking
    ruff check . && ruff format .  # Linting

Frontend (React/TypeScript)
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

    pnpm install              # Install dependencies
    pnpm dev                  # Run Vite dev server (HMR)
    pnpm build                # Build all apps
    pnpm lint                 # Lint all apps
    pnpm typecheck            # Type check all apps
    pnpm format               # Format with Prettier

    # Generate API client (Django must be running)
    cd apps/platform_django && pnpm openapi-ts

Parallel Development with Worktrees
-----------------------------------

Work on several features at once. Worktrees share this machine's Postgres and Redis
rather than each running a stack, and isolate by database name and Redis index.

**Creating a new worktree**::

    claude --worktree feature-branch

This:

- Creates a git worktree at ``.claude/worktrees/feature-branch``
- Generates ``.env`` with its own database name, Redis index and application ports
- Installs Python and frontend dependencies

**Check what this worktree got**::

    just ports
    # Django:    http://localhost:8001
    # Vite:      http://localhost:5174
    # Database:  platform_django_feature_branch on localhost:5432
    # Redis:     index 1 on localhost:6379

**Start development**::

    just up     # Start the shared services, create this worktree's database
    just serve  # Run Django on this worktree's port
    pnpm dev    # Start the Vite dev server

**Database considerations**: each worktree gets its own database on the shared
Postgres, created by ``just up``. Run ``just manage migrate`` in each worktree.

See :doc:`/5-ai-development/claude-code-workflow` for the full parallel development workflow.

API Client Generation
---------------------

When the Django API changes, regenerate the TypeScript client:

1. Ensure Django is running (``just serve``)
2. Generate the client::

       cd apps/platform_django
       pnpm openapi-ts

This creates typed React Query hooks in ``src/services/platform_django/``.

See :doc:`/4-frontend-guides/type-safe-api` for details.

Environment Files
-----------------

``.env`` is the one generated environment file: credentials, configuration, and
whatever this worktree was allocated. There is no second, layered file.

Django reads ``.env`` directly, so no shell hook is needed for anything to be
correct. mise also loads it for ``mise exec`` and for an activated shell.

**Keeping .env in sync after pulling changes**:

When ``.env.example`` changes upstream, a post-merge hook will warn you.
Run ``just env-refresh`` to merge new variables into your ``.env`` without overwriting your
existing values::

    just env-refresh          # Additive merge (preserves your overrides)

See :doc:`configuration` for complete variable reference.

Troubleshooting
---------------

Pre-commit Hook Failures
^^^^^^^^^^^^^^^^^^^^^^^^

Pre-commit hooks enforce code quality. If commits are blocked:

1. **Read the error message** --- it tells you what failed and how to fix it
2. **Common fixes**:

   - ``ruff`` errors: Run ``ruff check . --fix`` then ``ruff format .``
   - ``mypy`` errors: Type annotation issues --- see the file and line number
   - ``eslint`` errors: Run ``pnpm lint --fix``

3. Stage fixes and commit again

See :doc:`/6-code-quality/linting-formatting` for details.

Port Conflicts
^^^^^^^^^^^^^^

If you see "port already in use":

1. Check if another worktree is using the port: ``just ports``
2. Stop processes on that port: ``lsof -i :8000`` then ``kill <PID>``
3. Or use a different worktree with different ports

Tool Reference
--------------

``bin/bootstrap`` installs all required tools automatically. This section is for
troubleshooting.

System Requirements
^^^^^^^^^^^^^^^^^^^

- **Operating System**: macOS (Intel or Apple Silicon) or Linux
- **Memory**: 8GB minimum, 16GB recommended
- **Disk Space**: 10GB for dependencies, containers, and builds

Required Tools
^^^^^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Tool
     - Purpose
     - Where it is pinned
   * - **mise**
     - Installs the toolchain on macOS and Linux
     - Installed by ``bin/bootstrap`` from https://mise.run
   * - **Node.js**
     - Frontend runtime
     - ``.nvmrc`` --- mise reads it
   * - **Python**
     - Backend runtime
     - ``.python-version`` --- uv reads it and provisions the interpreter
   * - **pnpm**
     - Node.js package manager
     - ``packageManager`` in ``package.json``, installed via corepack
   * - **uv**
     - Python package manager
     - Not pinned --- ``bin/bootstrap`` uses whichever is on ``PATH``, and
       installs the current release from Astral if there is none
   * - **just**
     - Command runner (like make)
     - ``mise.toml``, from the npm registry
   * - **lefthook**
     - Git hooks for code quality
     - ``mise.toml``, from the npm registry

The two version files stay authoritative rather than being folded into
``mise.toml``, because the deployment platform reads the same files to choose
the runtimes it builds with.

Nothing in the toolchain resolves through GitHub's API. mise's default backend
looks each pinned version up at ``api.github.com``, which is unauthenticated and
rate-limited per IP, so on shared egress --- a cloud agent VM, a NAT'd CI runner
--- installs fail for reasons that have nothing to do with this project. ``just``
and ``lefthook`` therefore come from the npm registry, which has no such limit,
and Node comes from ``nodejs.org`` directly. uv ships only from GitHub releases,
so it is not a mise tool at all: every environment that matters already carries
it, and Astral's installer builds its download URL without asking the API.

Shell Configuration
^^^^^^^^^^^^^^^^^^^

``just setup`` adds mise activation to your shell profile. It is a convenience
only --- without it, prefix commands with ``mise exec --``. To add it by hand::

    eval "$(mise activate zsh)"

Verify Installation
^^^^^^^^^^^^^^^^^^^

::

    python --version      # 3.13.x
    node --version        # v24.x (matches .nvmrc)
    pnpm --version        # 11.x
    just --version
    docker --version

IDE Setup
^^^^^^^^^

**VS Code/Cursor** recommended extensions:

- Python, Pylance, Ruff
- ESLint, Prettier
- Tailwind CSS IntelliSense

Workspace settings are in ``.vscode/settings.json``.

**PyCharm**: Enable Python 3.13 interpreter, configure Ruff as external tool, enable Django support.

Next Steps
----------

1. **Explore the codebase**: Start with ``platform_django/users/``
2. **Read the architecture guide**: :doc:`/2-architecture/module-structure`
3. **Run the tests**: ``pytest``
