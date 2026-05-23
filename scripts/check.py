#!/usr/bin/env python3
"""Run sync check, validation, tests, then validation again."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

COMMANDS = [
    [sys.executable, "scripts/sync_guidelines.py", "--check"],
    [sys.executable, "scripts/validate.py"],
    [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
    [sys.executable, "scripts/validate.py"],
]

JUNK_DIR_NAMES = (
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
)

JUNK_FILE_GLOBS = (
    "*.pyc",
    ".DS_Store",
)


def clean_junk_files() -> None:
    dirs_to_remove = set()
    for dir_name in JUNK_DIR_NAMES:
        for path in ROOT.rglob(dir_name):
            if path.is_dir():
                dirs_to_remove.add(path)

    for path in sorted(dirs_to_remove, key=lambda p: len(p.parts), reverse=True):
        if path.is_symlink() or path.is_file():
            path.unlink(missing_ok=True)
            continue
        shutil.rmtree(path, ignore_errors=True)

    for glob_pattern in JUNK_FILE_GLOBS:
        for path in ROOT.rglob(glob_pattern):
            if path.is_file() or path.is_symlink():
                path.unlink(missing_ok=True)


def run_command(cmd: list[str], env: dict[str, str]) -> int:
    print("+", " ".join(cmd), flush=True)
    result = subprocess.run(cmd, cwd=ROOT, env=env)
    return result.returncode


def main() -> int:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    clean_junk_files()

    for index, cmd in enumerate(COMMANDS):
        return_code = run_command(cmd, env)
        if return_code != 0:
            return return_code

        # Unit tests may leave caches depending on local tooling/plugins.
        if index == 2:
            clean_junk_files()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
