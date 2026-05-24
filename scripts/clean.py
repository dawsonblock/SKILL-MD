#!/usr/bin/env python3
"""Remove generated artifacts and cache files from the repository."""

from __future__ import annotations

from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]

DIR_NAMES = {
    "dist",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}

FILE_NAMES = {
    ".DS_Store",
}

FILE_PREFIXES = {
    "._",
}

FILE_SUFFIXES = {
    ".pyc",
    ".pyo",
}


def clean(root: Path = ROOT) -> None:
    for path in sorted(root.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        if path.is_dir() and path.name in DIR_NAMES:
            shutil.rmtree(path, ignore_errors=True)
        elif path.is_file() or path.is_symlink():
            if path.name in FILE_NAMES:
                path.unlink(missing_ok=True)
            elif any(path.name.startswith(prefix) for prefix in FILE_PREFIXES):
                path.unlink(missing_ok=True)
            elif any(path.name.endswith(suffix) for suffix in FILE_SUFFIXES):
                path.unlink(missing_ok=True)

    macos = root / "__MACOSX"
    if macos.exists():
        shutil.rmtree(macos, ignore_errors=True)


def main() -> int:
    clean()
    print("Cleaned generated artifacts and cache files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
