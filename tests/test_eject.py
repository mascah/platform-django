"""Drive bin/eject against a throwaway repository.

Ejecting is one way and touches every file that names the template, so the
things worth asserting are that it renames what it should, leaves the pointers
to the template's own repository intact, and keeps the environment contract —
identity stays data after ejecting, only the package stops being the template's.
"""

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
EJECT = REPO_ROOT / "bin" / "eject"

# A miniature of the real rename surface: the package, the workspace app, the
# template file, settings that name them, and the three ways the template's own
# repository gets referenced.
FILES = {
    "platform_django/__init__.py": '"""The platform_django package."""\n',
    "platform_django/templates/apps/platform_django.html": (
        "<title>Platform Django</title>\n"
    ),
    "apps/platform_django/package.json": '{\n  "name": "platform_django"\n}\n',
    "apps/platform_django/vite.config.ts": (
        "export default { base: '/static/platform_django' };\n"
    ),
    "config/settings.py": (
        'INSTALLED_APPS = ["platform_django.users"]\n'
        'DJANGO_VITE = {"platform_django": {}}\n'
    ),
    ".env.example": (
        'PROJECT_SLUG=platform_django\nPROJECT_DISPLAY_NAME="Platform Django"\n'
    ),
    "app.json": '{\n  "name": "platform-django",\n  "value": "Platform Django"\n}\n',
    "CONTEXT.md": "# platform-django\n\nA project.\n",
    "README.md": (
        "# Platform Django\n\n"
        "git clone https://github.com/mascah/platform-django.git acme-app\n"
        "git remote add template https://github.com/mascah/platform-django.git\n"
        "See https://platform-django-template.readthedocs.io/ for docs.\n"
    ),
    "docs/agents/issue-tracker.md": "Issues live in `mascah/platform-django`.\n",
    "docs/tree.rst": "    platform-django/\n        platform_django/\n",
    # Tests the script that ejecting deletes, so it has to go with it —
    # otherwise the ejected project's suite fails on a missing bin/eject.
    "tests/test_eject.py": "EJECT = 'bin/eject'\n",
}

TEMPLATE_POINTERS = (
    "https://github.com/mascah/platform-django.git",
    "mascah/platform-django",
    "platform-django-template.readthedocs.io",
)


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.email=t@example.com", "-c", "user.name=Test", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


@pytest.fixture
def throwaway_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "acme"
    for relative, content in FILES.items():
        destination = repo / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content)

    eject = repo / "bin" / "eject"
    eject.parent.mkdir(parents=True, exist_ok=True)
    eject.write_bytes(EJECT.read_bytes())
    eject.chmod(EJECT.stat().st_mode)

    git(repo, "init", "-q", "-b", "main")
    git(
        repo,
        "remote",
        "add",
        "template",
        "https://github.com/mascah/platform-django.git",
    )
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "seed")
    return repo


def eject(repo: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(repo / "bin" / "eject"), *args],
        cwd=repo,
        capture_output=True,
        text=True,
    )


def read(repo: Path, relative: str) -> str:
    return (repo / relative).read_text()


def test_the_package_and_workspace_app_are_renamed(throwaway_repo: Path):
    assert eject(throwaway_repo, "acme_app").returncode == 0

    assert (throwaway_repo / "acme_app" / "__init__.py").exists()
    assert (throwaway_repo / "apps" / "acme_app" / "package.json").exists()
    assert (
        throwaway_repo / "acme_app" / "templates" / "apps" / "acme_app.html"
    ).exists()
    assert not (throwaway_repo / "platform_django").exists()
    assert not (throwaway_repo / "apps" / "platform_django").exists()


def test_references_to_the_package_follow_the_rename(throwaway_repo: Path):
    assert eject(throwaway_repo, "acme_app").returncode == 0

    assert 'INSTALLED_APPS = ["acme_app.users"]' in read(
        throwaway_repo, "config/settings.py"
    )
    assert "/static/acme_app" in read(throwaway_repo, "apps/acme_app/vite.config.ts")
    assert '"name": "acme_app"' in read(throwaway_repo, "apps/acme_app/package.json")


def test_the_display_name_defaults_to_the_slug_made_readable(throwaway_repo: Path):
    assert eject(throwaway_repo, "acme_app").returncode == 0

    assert 'PROJECT_DISPLAY_NAME="Acme App"' in read(throwaway_repo, ".env.example")
    assert '"value": "Acme App"' in read(throwaway_repo, "app.json")
    assert read(throwaway_repo, "README.md").startswith("# Acme App")


def test_a_display_name_may_be_given_explicitly(throwaway_repo: Path):
    assert eject(throwaway_repo, "acme_app", "ACME Rocket Sled").returncode == 0

    assert 'PROJECT_DISPLAY_NAME="ACME Rocket Sled"' in read(
        throwaway_repo, ".env.example"
    )
    # The slug is unaffected by the display name; they are separate values.
    assert "PROJECT_SLUG=acme_app" in read(throwaway_repo, ".env.example")


def test_the_environment_contract_survives(throwaway_repo: Path):
    """Identity stays data; only the package stops being the template's."""
    assert eject(throwaway_repo, "acme_app").returncode == 0

    env_example = read(throwaway_repo, ".env.example")
    assert "PROJECT_SLUG=" in env_example
    assert "PROJECT_DISPLAY_NAME=" in env_example


def test_this_projects_kebab_name_is_renamed(throwaway_repo: Path):
    assert eject(throwaway_repo, "acme_app").returncode == 0

    assert '"name": "acme-app"' in read(throwaway_repo, "app.json")
    assert read(throwaway_repo, "CONTEXT.md").startswith("# acme-app")
    assert "    acme-app/" in read(throwaway_repo, "docs/tree.rst")


def test_pointers_at_the_templates_repository_are_left_alone(throwaway_repo: Path):
    """Renaming these would mint URLs that look right and do not resolve."""
    result = eject(throwaway_repo, "acme_app")
    assert result.returncode == 0

    readme = read(throwaway_repo, "README.md")
    for pointer in TEMPLATE_POINTERS:
        assert pointer in readme, pointer
    assert "mascah/platform-django" in read(
        throwaway_repo, "docs/agents/issue-tracker.md"
    )

    # And it says which ones it kept, rather than leaving them to be discovered.
    assert "point at the template" in result.stdout
    assert "docs/agents/issue-tracker.md:1" in result.stdout


def test_the_template_remote_is_dropped_and_eject_removes_itself(throwaway_repo: Path):
    assert eject(throwaway_repo, "acme_app").returncode == 0

    assert "template" not in git(throwaway_repo, "remote").split()
    assert not (throwaway_repo / "bin" / "eject").exists()
    # Its test goes too, or the ejected project's suite fails on a missing script.
    assert not (throwaway_repo / "tests" / "test_eject.py").exists()
    # Staged, so `git reset --hard` still brings both back.
    assert "D  bin/eject" in git(throwaway_repo, "status", "--porcelain")


def test_a_dirty_tree_is_refused(throwaway_repo: Path):
    """`git reset --hard` is no undo at all if it discards uncommitted work."""
    (throwaway_repo / "CONTEXT.md").write_text("# uncommitted work\n")

    result = eject(throwaway_repo, "acme_app")

    assert result.returncode == 1
    assert "not clean" in result.stderr
    assert (throwaway_repo / "platform_django").exists()


@pytest.mark.parametrize("name", ["", "9lives", "acme-app!", "platform_django"])
def test_unusable_names_are_refused(throwaway_repo: Path, name: str):
    result = eject(throwaway_repo, name)

    assert result.returncode == 1
    assert (throwaway_repo / "platform_django").exists()


def test_any_spelling_of_the_name_reduces_to_one_package(throwaway_repo: Path):
    assert eject(throwaway_repo, "ACME App").returncode == 0

    assert (throwaway_repo / "acme_app" / "__init__.py").exists()
    assert '"name": "acme-app"' in read(throwaway_repo, "app.json")
