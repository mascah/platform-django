#!/usr/bin/env python3
"""Give every shell command an agent runs this worktree's values.

Claude Code's Bash tool does not run inside a shell that mise has activated, so
a command invoked directly — rather than through `just`, which loads .env
itself — would see whatever the ambient environment happens to hold rather than
this worktree's ports, database and Redis index.

mise already owns environment loading (mise.toml points `_.file` at .env), so
the whole job is asking it for the current directory's environment first. That
is the one line below; everything else is the hook envelope.

A machine without mise gets no prefix, because bin/bootstrap not having run yet
is not a reason to fail every command.
"""

import json
import shutil
import sys

PREFIX = 'eval "$(mise env -s bash)" 2>/dev/null\n'


command = json.load(sys.stdin).get("tool_input", {}).get("command", "")

if command and not command.startswith(PREFIX) and shutil.which("mise"):
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "updatedInput": {"command": PREFIX + command},
            }
        },
        sys.stdout,
    )
