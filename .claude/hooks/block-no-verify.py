#!/usr/bin/env python3
"""Block git commit/push commands with --no-verify flag."""

import json
import re
import sys

data = json.load(sys.stdin)
command = data.get("tool_input", {}).get("command", "")

if re.search(r"\bgit\s+(commit|push)\b.*--no-verify", command):
    print(  # noqa: T201
        "Blocked: --no-verify flag is not allowed. Git hooks must run.",
        file=sys.stderr,
    )
    sys.exit(2)

sys.exit(0)
