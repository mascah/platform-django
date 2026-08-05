"""Drive bin/provision against a fake Heroku CLI and a local push target.

app.json is the only place a deployment's shape is written down, and this script
is the only thing that applies it, so what these assert is the translation: that
every declared buildpack, add-on, configuration variable and process reaches the
command line, that a generated secret is generated rather than passed through as
the word "secret", and that the four steps whose order Heroku constrains stay in
that order.

Nothing here reaches the network. `heroku` is a shim on PATH that records its
arguments, and the push target is a bare repository in the same tmp_path.
"""

import json
import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

MANIFEST = {
    "name": "example-app",
    "stack": "heroku-24",
    "buildpacks": [{"url": "heroku/nodejs"}, {"url": "heroku/python"}],
    "addons": [
        {"plan": "heroku-postgresql:essential-0"},
        {"plan": "heroku-redis:mini"},
    ],
    "env": {
        "PROJECT_SLUG": {"description": "literal", "value": "example"},
        "DISPLAY": {"description": "spaces survive", "value": "Example App"},
        "DJANGO_SECRET_KEY": {"description": "generated", "generator": "secret"},
        "SENTRY_DSN": {"description": "optional", "required": False},
        "TYPOED": {"description": "unsupported", "generator": "sercet"},
        "BOTH": {"description": "literal wins", "value": "kept", "generator": "secret"},
    },
    "formation": {"web": {"quantity": 1, "size": "eco"}},
}

# apps:info decides whether the app already exists, so its exit status is what
# selects between the create path and configuring one in place.
HEROKU_SHIM = """#!/usr/bin/env bash
if [[ "$1" == "apps:info" ]]; then exit {apps_info_status}; fi
printf '%s\\n' "$*" >> "$HEROKU_LOG"
"""


def shim(directory: Path, apps_info_status: int = 1) -> Path:
    """Put a recording `heroku` on PATH; status 0 means the app already exists."""
    directory.mkdir(exist_ok=True)
    executable = directory / "heroku"
    executable.write_text(HEROKU_SHIM.format(apps_info_status=apps_info_status))
    executable.chmod(0o755)
    return directory


@pytest.fixture
def project(tmp_path: Path) -> Path:
    """A git repository carrying bin/provision, a manifest, and somewhere to push."""
    repo = tmp_path / "project"
    (repo / "bin").mkdir(parents=True)

    source = REPO_ROOT / "bin" / "provision"
    destination = repo / "bin" / "provision"
    destination.write_bytes(source.read_bytes())
    destination.chmod(source.stat().st_mode)

    (repo / "app.json").write_text(json.dumps(MANIFEST))

    git = ["git", "-c", "user.email=t@example.com", "-c", "user.name=Test"]
    subprocess.run([*git, "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run([*git, "add", "-A"], cwd=repo, check=True)
    subprocess.run([*git, "commit", "-qm", "seed"], cwd=repo, check=True)

    # The script runs `heroku git:remote`, which the shim swallows, so the remote
    # it would have created is pre-made here and points at a bare repository.
    target = tmp_path / "target.git"
    subprocess.run(["git", "init", "-q", "--bare", str(target)], check=True)
    subprocess.run(
        ["git", "remote", "add", "heroku", str(target)], cwd=repo, check=True
    )
    return repo


def provision(
    repo: Path, *args: str, path_extra: Path | None = None
) -> subprocess.CompletedProcess:
    """Run bin/provision, with `heroku` shimmed onto PATH when asked."""
    env = {
        "PATH": f"{path_extra}:/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin"
        if path_extra
        else "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin",
        "HOME": str(repo.parent),
    }
    if path_extra:
        env["HEROKU_LOG"] = str(repo.parent / "heroku.log")
    return subprocess.run(
        [str(repo / "bin" / "provision"), *args],
        cwd=repo,
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )


def test_dry_run_emits_the_manifest_in_the_order_heroku_requires(project: Path) -> None:
    lines = provision(project, "--dry-run").stdout.splitlines()
    joined = "\n".join(lines)

    assert "heroku create example-app --stack heroku-24" in lines
    # Cleared before adding, or a second run builds the frontend twice.
    assert lines.index("heroku buildpacks:clear --app example-app") < lines.index(
        "heroku buildpacks:add heroku/nodejs --app example-app"
    )
    # Node before Python: collectstatic has to find what the frontend built.
    assert lines.index(
        "heroku buildpacks:add heroku/nodejs --app example-app"
    ) < lines.index("heroku buildpacks:add heroku/python --app example-app")
    for plan in ("heroku-postgresql:essential-0", "heroku-redis:mini"):
        assert f"heroku addons:create {plan} --app example-app" in lines

    config = next(line for line in lines if line.startswith("heroku config:set"))
    push = next(i for i, line in enumerate(lines) if line.startswith("git push"))
    scale = lines.index("heroku ps:scale web=1:eco --app example-app")

    # migrate runs in the release phase of the push, so configuration precedes it.
    assert lines.index(config) < push
    # A process type does not exist until a slug declares it.
    assert push < scale

    assert "PROJECT_SLUG=example" in config
    # A value with a space has to survive being pasted back, and this template's
    # own PROJECT_DISPLAY_NAME has one. Unquoted, the paste sets the first word
    # and fails on the second.
    assert '"DISPLAY=Example App"' in config
    # A dry run should stay copy-pasteable rather than printing a live secret,
    # so the quoting has to be double — single quotes would paste the
    # substitution instead of running it.
    assert '"DJANGO_SECRET_KEY=$(openssl rand -hex 32)"' in config
    # Declared optional, so it is the prototype tier's business to leave it unset.
    assert "SENTRY_DSN" not in joined
    assert "TYPOED" not in config
    # A variable declaring both reaches config:set once, as its literal —
    # twice and which one lands would be Heroku's decision, not the manifest's.
    assert config.count("BOTH=") == 1
    assert "BOTH=kept" in config


def test_unsupported_generator_is_reported_rather_than_dropped(project: Path) -> None:
    stderr = provision(project, "--dry-run").stderr
    assert "TYPOED" in stderr
    assert "unsupported generator" in stderr


def test_a_real_run_generates_a_secret_and_pushes(
    tmp_path: Path, project: Path
) -> None:
    provision(project, path_extra=shim(tmp_path / "shim"))
    recorded = (tmp_path / "heroku.log").read_text()

    # The bug this guards: tab is IFS whitespace, so a generator-only variable
    # arrives one field short and its generator is read as its value.
    secret = re.search(r"DJANGO_SECRET_KEY=(\S+)", recorded)
    assert secret, recorded
    assert re.fullmatch(r"[0-9a-f]{64}", secret.group(1)), secret.group(1)

    # ps:scale only runs if the push before it succeeded, and the push is real.
    assert "ps:scale web=1:eco" in recorded
    target = tmp_path / "target.git"
    pushed = subprocess.run(
        ["git", "--git-dir", str(target), "rev-parse", "refs/heads/main"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert pushed.stdout.strip()


def test_an_existing_app_is_configured_in_place(tmp_path: Path, project: Path) -> None:
    """Six steps run against a billed account and any one can fail, so a second
    run has to configure what is there rather than failing on create."""
    provision(project, path_extra=shim(tmp_path / "shim", apps_info_status=0))
    recorded = (tmp_path / "heroku.log").read_text()

    # `addons:create` is a create too, so this has to be the app one specifically.
    assert not any(line.startswith("create ") for line in recorded.splitlines()), (
        recorded
    )
    # buildpacks:add appends, so without the clear a second run would build the
    # frontend twice.
    assert recorded.index("buildpacks:clear") < recorded.index(
        "buildpacks:add heroku/nodejs"
    )
    assert recorded.count("buildpacks:add heroku/nodejs") == 1
    assert "config:set" in recorded
    assert "ps:scale web=1:eco" in recorded
