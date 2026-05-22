#!/usr/bin/env python3
"""Repository validation checks."""

from __future__ import annotations

import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
BEGIN = "<!-- BEGIN CANONICAL BODY -->"
END = "<!-- END CANONICAL BODY -->"


def normalize(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.strip().split("\n")]
    return "\n".join(lines).strip()


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def extract_marked_body(path: Path, text: str) -> str:
    if BEGIN not in text or END not in text:
        raise ValueError(f"Missing canonical body markers in {path.relative_to(ROOT)}")
    start = text.index(BEGIN) + len(BEGIN)
    end = text.index(END)
    return text[start:end]


def check_exists(errors: list[str], rel_path: str) -> Path:
    path = ROOT / rel_path
    if not path.exists():
        errors.append(f"Missing required file: {rel_path}")
    return path


def check_plugin_metadata(errors: list[str]) -> None:
    plugin_path = check_exists(errors, ".claude-plugin/plugin.json")
    marketplace_path = check_exists(errors, ".claude-plugin/marketplace.json")
    if errors:
        return

    try:
        plugin = json.loads(read(plugin_path))
        marketplace = json.loads(read(marketplace_path))
    except json.JSONDecodeError as exc:
        errors.append(f"Invalid plugin JSON: {exc}")
        return

    required_plugin_keys = ["name", "description", "version", "license", "skills"]
    for key in required_plugin_keys:
        if key not in plugin:
            errors.append(f"plugin.json missing key: {key}")

    if "metadata" not in marketplace or "plugins" not in marketplace:
        errors.append("marketplace.json missing metadata/plugins")
        return

    marketplace_version = marketplace.get("metadata", {}).get("version")
    plugin_version = plugin.get("version")
    listed_plugins = marketplace.get("plugins", [])
    listed_version = listed_plugins[0].get("version") if listed_plugins else None

    if not plugin_version or not marketplace_version or not listed_version:
        errors.append("Missing one or more version fields in plugin metadata")
        return

    if plugin_version != marketplace_version or plugin_version != listed_version:
        errors.append(
            "Version mismatch across plugin metadata files. "
            f"plugin.json={plugin_version}, marketplace.metadata={marketplace_version}, marketplace.plugins[0]={listed_version}"
        )


def check_cursor_frontmatter(errors: list[str]) -> None:
    mdc_path = check_exists(errors, ".cursor/rules/karpathy-guidelines.mdc")
    if not mdc_path.exists():
        return

    text = read(mdc_path)
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        errors.append("Cursor rule is missing YAML frontmatter block")
        return

    frontmatter = match.group(1)
    if "alwaysApply: true" not in frontmatter:
        errors.append("Cursor rule frontmatter must contain alwaysApply: true")
    if "description:" not in frontmatter:
        errors.append("Cursor rule frontmatter must contain description")


def check_guideline_sections(errors: list[str]) -> None:
    canonical_path = check_exists(errors, "docs/guidelines.md")
    if not canonical_path.exists():
        return

    text = read(canonical_path)
    required_sections = [
        "## 1. Think Before Coding",
        "## 2. Simplicity First",
        "## 3. Surgical Changes",
        "## 4. Goal-Driven Execution",
        "**These guidelines are working if:**",
    ]
    for section in required_sections:
        if section not in text:
            errors.append(f"Canonical guidelines missing required section: {section}")


def check_canonical_sync(errors: list[str]) -> None:
    canonical_path = check_exists(errors, "docs/guidelines.md")
    targets = [
        "CLAUDE.md",
        ".cursor/rules/karpathy-guidelines.mdc",
        "skills/karpathy-guidelines/SKILL.md",
    ]
    if not canonical_path.exists():
        return

    canonical_text = read(canonical_path)
    try:
        canonical_body = normalize(extract_marked_body(canonical_path, canonical_text))
    except ValueError as exc:
        errors.append(str(exc))
        return

    for rel in targets:
        path = check_exists(errors, rel)
        if not path.exists():
            continue
        try:
            body = normalize(extract_marked_body(path, read(path)))
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if body != canonical_body:
            errors.append(f"Guideline body drift detected in {rel}. Run: python3 scripts/sync_guidelines.py")


def check_content_files(errors: list[str]) -> None:
    for rel in ["docs/guidelines.md", "README.zh.md", "CURSOR.md", "EXAMPLES.md"]:
        check_exists(errors, rel)


def check_forbidden_wording(errors: list[str]) -> None:
    cursor_path = ROOT / "CURSOR.md"
    if cursor_path.exists():
        cursor_text = read(cursor_path)
        forbidden_cursor_phrases = [
            "keep **[`CLAUDE.md`](CLAUDE.md)** and **[`.cursor/rules/karpathy-guidelines.mdc`](.cursor/rules/karpathy-guidelines.mdc)** in sync",
            "If the published skill/plugin text should match, update",
        ]
        for phrase in forbidden_cursor_phrases:
            if phrase in cursor_text:
                errors.append("CURSOR.md still contains outdated manual sync wording")
                break


def check_examples(errors: list[str]) -> None:
    examples_path = ROOT / "EXAMPLES.md"
    if not examples_path.exists():
        return

    text = read(examples_path)
    forbidden_patterns = [
        'logger.exception(f"Upload error for {file_path}: {e}")',
        "logger.exception(f'Upload error: {file_path}')\n         print",
    ]
    for pattern in forbidden_patterns:
        if pattern in text:
            errors.append(f"Malformed logging example pattern found in EXAMPLES.md: {pattern}")


def main() -> int:
    errors: list[str] = []

    check_plugin_metadata(errors)
    check_cursor_frontmatter(errors)
    check_content_files(errors)
    check_guideline_sections(errors)
    check_canonical_sync(errors)
    check_forbidden_wording(errors)
    check_examples(errors)

    if errors:
        print("Validation failed:")
        for err in errors:
            print(f"- {err}")
        return 1

    print("Validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
