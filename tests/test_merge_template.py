"""Drive bin/merge-template against two throwaway repositories.

The script settles what always settles the same way and stops at anything else,
so what these assert is where that line falls when a lockfile cannot be
regenerated. A manifest can merge cleanly and still not parse — two sides
adding the same key add it on different lines — and the locker is what finds
out. Discovering it that late has to leave a merge someone can finish, not an
abandoned half-resolved one.

Nothing here runs a real locker or reaches the network. `uv` is a shim on PATH
whose exit status is the case under test, and both repositories are ordinary
directories in tmp_path.
"""

import os
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

FAILING_UV = """#!/usr/bin/env bash
echo "TOML parse error: duplicate key" >&2
exit 2
"""

WORKING_UV = """#!/usr/bin/env bash
echo "locked" > uv.lock
"""


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run git in a repository, failing the test on a non-zero exit."""
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, text=True, check=True
    )


def commit(repo: Path, name: str, content: str) -> None:
    (repo / name).write_text(content)
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", content.strip())


@pytest.fixture
def child(tmp_path: Path) -> Path:
    """A clone whose uv.lock conflicts with its template's, and nothing else."""
    template = tmp_path / "template"
    (template / "bin").mkdir(parents=True)
    source = REPO_ROOT / "bin" / "merge-template"
    script = template / "bin" / "merge-template"
    script.write_bytes(source.read_bytes())
    script.chmod(source.stat().st_mode)
    (template / "pyproject.toml").write_text('[project]\nname = "throwaway"\n')
    git(template, "init", "-q", "-b", "main")
    git(template, "config", "user.email", "t@example.com")
    git(template, "config", "user.name", "Test")
    commit(template, "uv.lock", "base\n")

    child = tmp_path / "child"
    git(tmp_path, "clone", "-q", str(template), str(child))
    git(child, "config", "user.email", "c@example.com")
    git(child, "config", "user.name", "Child")

    # The same line on both sides: uv.lock conflicts, pyproject.toml does not.
    commit(template, "uv.lock", "template\n")
    commit(child, "uv.lock", "child\n")
    return child


def merge(child: Path, uv_source: str) -> subprocess.CompletedProcess[str]:
    """Run the script with `uv` shimmed to the behaviour under test."""
    shims = child.parent / "shims"
    shims.mkdir(exist_ok=True)
    executable = shims / "uv"
    executable.write_text(uv_source)
    executable.chmod(0o755)
    environment = {**os.environ, "PATH": f"{shims}{os.pathsep}{os.environ['PATH']}"}
    return subprocess.run(
        [str(child / "bin" / "merge-template"), "origin", "main"],
        cwd=child,
        capture_output=True,
        text=True,
        env=environment,
        check=False,
    )


def unmerged(repo: Path, path: str) -> bool:
    return bool(git(repo, "ls-files", "--unmerged", "--", path).stdout)


def test_a_failed_lock_leaves_a_merge_someone_can_finish(child: Path):
    """The locker's failure is a result to report, not a reason to bail out."""
    result = merge(child, FAILING_UV)

    assert result.returncode == 1
    assert (child / ".git" / "MERGE_HEAD").exists()
    assert unmerged(child, "uv.lock")


def test_a_failed_lock_says_what_to_do_next(child: Path):
    result = merge(child, FAILING_UV)

    assert "uv lock && git add uv.lock" in result.stderr
    assert "Conflicts remain" in result.stderr


def test_a_successful_lock_still_commits_the_merge(child: Path):
    result = merge(child, WORKING_UV)

    assert result.returncode == 0, result.stderr
    assert not (child / ".git" / "MERGE_HEAD").exists()
    assert (child / "uv.lock").read_text() == "locked\n"
