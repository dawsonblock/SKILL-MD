#!/usr/bin/env python3
"""Run sync check, validation, tests, then validation again."""

from __future__ import annotations

import importlib.util as _ilu
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

_spec = _ilu.spec_from_file_location("clean", Path(__file__).resolve().parent / "clean.py")
_clean = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_clean)


def run_command(cmd: list[str], env: dict[str, str]) -> int:
    print("+", " ".join(cmd), flush=True)
    result = subprocess.run(cmd, cwd=ROOT, env=env)
    return result.returncode


def main() -> int:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    _clean.clean(root=ROOT)

    for index, cmd in enumerate(COMMANDS):
        return_code = run_command(cmd, env)
        if return_code != 0:
            return return_code

        # Unit tests may leave caches depending on local tooling/plugins.
        if index == 2:
            _clean.clean(root=ROOT)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
