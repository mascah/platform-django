"""Drive bin/worktree-create against a throwaway repository.

The only non-obvious thing worktree creation does is decide what a new worktree
may take from a machine it shares with everything else, so that is what these
assert: a complete .env, and ports that collide with neither a sibling worktree
nor an unrelated process.

Nothing here touches Django, Postgres or Redis — the script is run as a
subprocess and its output is the .env it wrote.
"""

import socket
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SEEDED = (
    "bin/env-refresh",
    "bin/worktree-create",
    "bin/worktree-destroy",
    ".env.example",
)


def read_env(path: Path) -> dict[str, str]:
    """Parse a KEY=VALUE file, ignoring comments and blanks."""
    values = {}
    for line in path.read_text().splitlines():
        if line.strip() and not line.lstrip().startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            values[key] = value
    return values


@pytest.fixture
def throwaway_repo(tmp_path: Path) -> Path:
    """A git repository carrying just enough of the template to create worktrees."""
    repo = tmp_path / "throwaway_project"
    (repo / "bin").mkdir(parents=True)

    for relative in SEEDED:
        source = REPO_ROOT / relative
        destination = repo / relative
        destination.write_bytes(source.read_bytes())
        destination.chmod(source.stat().st_mode)

    git = ["git", "-c", "user.email=t@example.com", "-c", "user.name=Test"]
    subprocess.run([*git, "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run([*git, "add", "-A"], cwd=repo, check=True)
    subprocess.run([*git, "commit", "-qm", "seed"], cwd=repo, check=True)
    return repo


def create_worktree(repo: Path, name: str) -> Path:
    """Run the script the way a shell would, and return the path it reports."""
    result = subprocess.run(
        [str(repo / "bin" / "worktree-create"), name],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    )
    return Path(result.stdout.strip())


def test_worktree_env_is_complete(throwaway_repo: Path):
    worktree = create_worktree(throwaway_repo, "alpha")

    template_keys = read_env(throwaway_repo / ".env.example").keys()
    generated = read_env(worktree / ".env")

    assert template_keys <= generated.keys()
    assert all(generated[key] for key in template_keys)


def test_second_worktree_takes_different_ports(throwaway_repo: Path):
    alpha = read_env(create_worktree(throwaway_repo, "alpha") / ".env")
    beta = read_env(create_worktree(throwaway_repo, "beta") / ".env")

    assert alpha["DJANGO_PORT"] != beta["DJANGO_PORT"]
    assert alpha["VITE_PORT"] != beta["VITE_PORT"]


def test_worktrees_are_isolated_by_database_and_redis_index(throwaway_repo: Path):
    alpha = read_env(create_worktree(throwaway_repo, "alpha") / ".env")
    beta = read_env(create_worktree(throwaway_repo, "beta") / ".env")

    assert alpha["POSTGRES_DB"] != beta["POSTGRES_DB"]
    assert alpha["REDIS_DB"] != beta["REDIS_DB"]
    # The slug is the project, not the worktree, so it must not drift.
    assert alpha["PROJECT_SLUG"] == beta["PROJECT_SLUG"] == "throwaway_project"


def test_a_port_bound_by_another_process_is_not_handed_out(throwaway_repo: Path):
    """The sibling .env files know nothing about the rest of the machine."""
    default_django_port = int(read_env(throwaway_repo / ".env.example")["DJANGO_PORT"])

    with socket.socket() as occupied:
        try:
            occupied.bind(("127.0.0.1", default_django_port))
        except OSError:
            pytest.skip(f"port {default_django_port} is already in use")
        occupied.listen(1)

        allocated = read_env(create_worktree(throwaway_repo, "alpha") / ".env")

    assert int(allocated["DJANGO_PORT"]) != default_django_port
