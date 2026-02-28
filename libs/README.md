# libs/ — Isolated Python Packages

This directory holds standalone Python packages managed as UV workspace members.

## Purpose

Packages in `libs/` are:

- **Django-free**: They must not import Django or the main `platform_django` package.
- **Independently testable**: Each package has its own `tests/` directory.
- **Shared via workspace**: They are declared as UV workspace members in the root `pyproject.toml`.

## Creating a New Package

```bash
# 1. Scaffold the package
uv init --package libs/my-package

# 2. Add to root pyproject.toml dependencies and [tool.uv.sources]
#    "my-package" = { workspace = true }

# 3. Sync dependencies
uv sync
```

## Running Tests

```bash
just libs-test              # All libs
just libs-test-one my-package  # Specific lib
```
