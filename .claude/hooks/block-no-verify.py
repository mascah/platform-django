#!/usr/bin/env python3
"""Block commands that bypass git hooks (--no-verify, LEFTHOOK=0)."""

import json
import re
import sys

data = json.load(sys.stdin)
command = data.get("tool_input", {}).get("command", "")


def deny(reason: str) -> None:
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        },
        sys.stdout,
    )
    sys.exit(0)


if re.search(r"\bgit\s+(commit|push)\b.*--no-verify", command):
    deny("--no-verify flag is not allowed. Git hooks must run.")

if re.search(r"\bLEFTHOOK=0\b", command):
    deny("LEFTHOOK=0 is not allowed. Git hooks must run.")

sys.exit(0)
