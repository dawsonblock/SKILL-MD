#!/usr/bin/env python3
"""Build a verified release archive for this repository."""

from __future__ import annotations

import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RELEASE_ROOT_NAME = f"{ROOT.name}-main"
ARCHIVE_NAME = f"{RELEASE_ROOT_NAME}-fixed.zip"
OUTPUT_PATH = ROOT / "dist" / ARCHIVE_NAME

FORBIDDEN_PATH_PARTS = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "node_modules",
    ".git",
}

FORBIDDEN_FILE_SUFFIXES = {
    ".pyc",
}

FORBIDDEN_FILE_NAMES = {
    ".DS_Store",
}


def clean_junk_files(base: Path) -> None:
    dirs_to_remove = set()
    for path_part in ("__pycache__", ".pytest_cache", ".mypy_cache"):
        for path in base.rglob(path_part):
            if path.is_dir():
                dirs_to_remove.add(path)

    for path in sorted(dirs_to_remove, key=lambda p: len(p.parts), reverse=True):
        if path.is_symlink() or path.is_file():
            path.unlink(missing_ok=True)
            continue
        shutil.rmtree(path, ignore_errors=True)

    for glob_pattern in ("*.pyc", ".DS_Store"):
        for path in base.rglob(glob_pattern):
            if path.is_file() or path.is_symlink():
                path.unlink(missing_ok=True)


def run_check(cwd: Path) -> int:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    cmd = [sys.executable, "scripts/check.py"]
    print("+", " ".join(cmd), f"(cwd={cwd})", flush=True)
    result = subprocess.run(cmd, cwd=cwd, env=env)
    return result.returncode


def should_include(rel_path: Path) -> bool:
    if not rel_path.parts:
        return False

    if rel_path.parts[0] == "dist":
        return False

    if any(part in FORBIDDEN_PATH_PARTS for part in rel_path.parts):
        return False

    if rel_path.name in FORBIDDEN_FILE_NAMES:
        return False

    if any(rel_path.name.endswith(suffix) for suffix in FORBIDDEN_FILE_SUFFIXES):
        return False

    return True


def create_archive(source_root: Path, output_path: Path) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    file_count = 0
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source_root.rglob("*")):
            if not path.is_file():
                continue

            rel_path = path.relative_to(source_root)
            if not should_include(rel_path):
                continue

            arcname = PurePosixPath(RELEASE_ROOT_NAME, *rel_path.parts)
            archive.write(path, arcname=str(arcname))
            file_count += 1

    return file_count


def verify_archive(output_path: Path) -> int:
    with tempfile.TemporaryDirectory(prefix="skill-md-release-") as temp_dir:
        temp_root = Path(temp_dir)
        with zipfile.ZipFile(output_path, "r") as archive:
            archive.extractall(temp_root)

        extracted_root = temp_root / RELEASE_ROOT_NAME
        if not extracted_root.exists():
            print(
                f"Expected extracted root not found: {extracted_root}",
                file=sys.stderr,
            )
            return 1

        return run_check(extracted_root)


def main() -> int:
    print("Running source checks...", flush=True)
    source_result = run_check(ROOT)
    if source_result != 0:
        return source_result

    print("Cleaning junk files before packaging...", flush=True)
    clean_junk_files(ROOT)

    print(f"Creating archive: {OUTPUT_PATH}", flush=True)
    file_count = create_archive(ROOT, OUTPUT_PATH)

    print("Verifying extracted archive...", flush=True)
    archive_result = verify_archive(OUTPUT_PATH)
    if archive_result != 0:
        return archive_result

    print(f"Release archive ready: {OUTPUT_PATH}", flush=True)
    print(f"Archive entries: {file_count}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
