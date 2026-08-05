#!/usr/bin/env python3
"""Give every shell command an agent runs this worktree's values.

Claude Code's Bash tool does not run inside a shell that mise has activated, so
a command invoked directly — rather than through `just`, which loads .env
itself — would see whatever the ambient environment happens to hold rather than
this worktree's ports, database and Redis index.

mise already owns environment loading (mise.toml points `_.file` at .env), so
the whole job is asking it for the command's directory. This hook asks here, in
Python, and pastes the answer in front of the command as literal `export` lines.

The shorter version this replaced asked from inside the command itself, by
prefixing `eval "$(mise env -s bash)"`. That cannot stay: a session isolated in
a worktree refuses to run any command it cannot statically certify as staying
inside that worktree, and a command substitution feeding `eval` is uncertifiable
by construction. Every Bash call in such a session was refused, down to `pwd`.
Literal `export` lines are certifiable, so keep the substitution out of here.
This costs no extra process — the substitution forked mise once per command too.

Prefixing rather than wrapping is also deliberate. `mise exec -- <command>`
needs no substitution either, but it wraps a single process, so the right-hand
side of any `&&`, `|` or `;` would silently fall back to the ambient
environment and address the wrong database.

A machine without mise, or a config mise declines to read, gets no prefix:
neither bin/bootstrap having not run yet nor an untrusted mise.toml is a reason
to fail every command. mise's stderr is dropped through the subprocess call
rather than a shell redirect, because a redirect is the other construct the
isolation guard rejects.
"""

import json
import shutil
import subprocess
import sys

payload = json.load(sys.stdin)
command = payload.get("tool_input", {}).get("command", "")
executable = shutil.which("mise")

if command and executable:
    # S603: every argument is a literal and the executable came from which().
    mise = subprocess.run(  # noqa: S603
        [executable, "env", "-s", "bash"],
        cwd=payload.get("cwd") or None,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    prefix = mise.stdout.strip()
    if mise.returncode == 0 and prefix and not command.startswith(prefix):
        json.dump(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "updatedInput": {"command": f"{prefix}\n{command}"},
                }
            },
            sys.stdout,
        )
