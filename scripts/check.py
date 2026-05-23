#!/usr/bin/env python3
"""Run sync check, validation, tests, then validation again."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

COMMANDS = [
    [sys.executable, "scripts/sync_guidelines.py", "--check"],
    [sys.executable, "scripts/validate.py"],
    [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
    [sys.executable, "scripts/validate.py"],
]


def main() -> int:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    for cmd in COMMANDS:
        print("+", " ".join(cmd))
        result = subprocess.run(cmd, cwd=ROOT, env=env)
        if result.returncode != 0:
            return result.returncode

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
