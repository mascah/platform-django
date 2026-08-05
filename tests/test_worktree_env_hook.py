"""Drive .claude/hooks/worktree-env.py the way Claude Code's Bash tool would.

The hook's one job is pasting mise's environment in front of a command, and the
only way it can get that wrong badly enough to matter is by pasting shell a
worktree-isolated session refuses to run — a command substitution, an `eval`, a
redirect. Such a session then rejects every command, down to `pwd`, so that is
what the first test pins.

mise is stubbed rather than installed: the hook's contract is with whatever
`mise env -s bash` prints, not with mise itself, and CI should not need a
trusted config to run these.
"""

import json
import os
import subprocess
from pathlib import Path

HOOK = Path(__file__).resolve().parent.parent / ".claude" / "hooks" / "worktree-env.py"
REFUSED_BY_THE_ISOLATION_GUARD = ("eval", "$(", "`", "2>", ">/")


def stub_mise(directory: Path, script: str) -> dict[str, str]:
    """Put a fake `mise` first on PATH and return the environment to run under."""
    binary = directory / "mise"
    binary.write_text(f"#!/bin/sh\n{script}\n")
    binary.chmod(0o755)
    return {**os.environ, "PATH": f"{directory}:{os.environ['PATH']}"}


def run_hook(command: str, env: dict[str, str]) -> str:
    """Return the command the hook wants run, which is the original if it declines."""
    payload = {"tool_input": {"command": command}, "cwd": str(HOOK.parent)}
    result = subprocess.run(
        [str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )
    if not result.stdout.strip():
        return command
    hook_output = json.loads(result.stdout)["hookSpecificOutput"]
    return hook_output["updatedInput"]["command"]


def test_the_prefix_is_shell_an_isolated_session_can_certify(tmp_path: Path):
    env = stub_mise(tmp_path, "echo \"export DJANGO_PORT='8010'\"")

    rewritten = run_hook("pwd", env)

    assert rewritten == "export DJANGO_PORT='8010'\npwd"
    assert not any(bad in rewritten for bad in REFUSED_BY_THE_ISOLATION_GUARD)


def test_a_command_still_runs_when_mise_will_not_answer(tmp_path: Path):
    """An unbootstrapped machine or untrusted config must not fail every command."""
    env = stub_mise(tmp_path, "exit 1")

    assert run_hook("pwd", env) == "pwd"
