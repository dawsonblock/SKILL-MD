#!/usr/bin/env python3
"""Repository validation checks."""

from __future__ import annotations

import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
BEGIN = "<!-- BEGIN CANONICAL BODY -->"
END = "<!-- END CANONICAL BODY -->"

REQUIRED_CANONICAL_PHRASES = [
    "State assumptions explicitly when they affect correctness",
    "Infer from code, tests, docs, and user context when the evidence is strong",
    "Ask only when missing information blocks a correct implementation",
    "No broad speculative error handling",
    "Handle realistic failure modes shown by the code path",
    "Verification Discipline",
    "Repo Repair Protocol",
    "Claim Boundaries",
    "Task Modes",
    "Output Discipline",
]

FORBIDDEN_PHRASES = [
    "State your assumptions explicitly. If uncertain, ask.",
    "No error handling for impossible scenarios.",
    "derived from Andrej Karpathy's observations",
    "查看我的新项目",
]

TEXT_FILES_TO_SCAN = [
    ROOT / "docs" / "guidelines.md",
    ROOT / "CLAUDE.md",
    ROOT / ".cursor" / "rules" / "karpathy-guidelines.mdc",
    ROOT / "skills" / "karpathy-guidelines" / "SKILL.md",
    ROOT / "README.md",
    ROOT / "README.zh.md",
    ROOT / "CURSOR.md",
    ROOT / "EXAMPLES.md",
    ROOT / "CHANGELOG.md",
]

JSON_TEXT_FILES_TO_SCAN = [
    ROOT / ".claude-plugin" / "plugin.json",
    ROOT / ".claude-plugin" / "marketplace.json",
]


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
    end = text.find(END, start)
    if end == -1:
        raise ValueError(
            f"Missing canonical body end marker after begin marker in {path.relative_to(ROOT)}"
        )
    return text[start:end]


def check_exists(errors: list[str], rel_path: str) -> Path:
    path = ROOT / rel_path
    if not path.exists():
        errors.append(f"Missing required file: {rel_path}")
    return path


def check_plugin_metadata(errors: list[str]) -> None:
    plugin_path = check_exists(errors, ".claude-plugin/plugin.json")
    marketplace_path = check_exists(errors, ".claude-plugin/marketplace.json")
    if not plugin_path.exists() or not marketplace_path.exists():
        return

    try:
        plugin = json.loads(read(plugin_path))
    except json.JSONDecodeError as exc:
        errors.append(f"Invalid plugin JSON ({plugin_path.relative_to(ROOT)}): {exc}")
        return

    try:
        marketplace = json.loads(read(marketplace_path))
    except json.JSONDecodeError as exc:
        errors.append(
            f"Invalid plugin JSON ({marketplace_path.relative_to(ROOT)}): {exc}"
        )
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
    plugin_name = plugin.get("name")
    listed_plugins = marketplace.get("plugins", [])
    listed_entry = None
    if isinstance(listed_plugins, list) and plugin_name:
        listed_entry = next(
            (
                item
                for item in listed_plugins
                if isinstance(item, dict) and item.get("name") == plugin_name
            ),
            None,
        )

    if listed_entry is None:
        errors.append(
            "marketplace.json plugins[] must include an entry matching plugin.json name"
        )
        return

    listed_version = listed_entry.get("version")

    if not plugin_version or not marketplace_version or not listed_version:
        errors.append("Missing one or more version fields in plugin metadata")
        return

    if plugin_version != marketplace_version or plugin_version != listed_version:
        errors.append(
            "Version mismatch across plugin metadata files. "
            "plugin.json="
            f"{plugin_version}, "
            "marketplace.metadata="
            f"{marketplace_version}, "
            "marketplace.plugins[name-match]="
            f"{listed_version}"
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
        "## Output Discipline",
        "**These guidelines are working if:**",
    ]
    for section in required_sections:
        if section not in text:
            errors.append(f"Canonical guidelines missing required section: {section}")

    for phrase in REQUIRED_CANONICAL_PHRASES:
        if phrase not in text:
            errors.append(f"Canonical guidelines missing required phrase: {phrase}")


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
            errors.append(
                f"Guideline body drift detected in {rel}. Run: python3 scripts/sync_guidelines.py"
            )


def check_content_files(errors: list[str]) -> None:
    for path in TEXT_FILES_TO_SCAN:
        if not path.exists():
            errors.append(f"Missing required file: {path.relative_to(ROOT)}")
    for path in JSON_TEXT_FILES_TO_SCAN:
        if not path.exists():
            errors.append(f"Missing required file: {path.relative_to(ROOT)}")


def check_forbidden_phrases(errors: list[str]) -> None:
    scan_paths = TEXT_FILES_TO_SCAN + JSON_TEXT_FILES_TO_SCAN
    for path in scan_paths:
        if not path.exists():
            continue
        text = read(path)
        for phrase in FORBIDDEN_PHRASES:
            if phrase in text:
                errors.append(
                    f"Forbidden phrase found in {path.relative_to(ROOT)}: {phrase}"
                )


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
            errors.append(
                f"Malformed logging example pattern found in EXAMPLES.md: {pattern}"
            )

    required_example_phrases = [
        "Add basic in-memory rate limiting for one endpoint",
        "Extract rate limiting into middleware",
        "test_sort_users_by_score_ties_are_deterministic",
        'assert [u["name"] for u in result] == ["Alice", "Charlie", "Bob"]',
        "logger.exception(f'Upload error: {file_path}')",
        'print(f"Error: {e}")',
    ]
    for phrase in required_example_phrases:
        if phrase not in text:
            errors.append(f"EXAMPLES.md missing required corrected content: {phrase}")


def check_readme_disclaimers(errors: list[str]) -> None:
    readme = ROOT / "README.md"
    readme_zh = ROOT / "README.zh.md"

    if readme.exists():
        text = read(readme)
        if "Not affiliated with or endorsed by Andrej Karpathy" not in text:
            errors.append("README.md missing non-affiliation disclaimer")

    if readme_zh.exists():
        text = read(readme_zh)
        if "与 Andrej Karpathy 无关" not in text and "未经其认可" not in text:
            errors.append("README.zh.md missing non-affiliation disclaimer")


def main() -> int:
    errors: list[str] = []

    check_plugin_metadata(errors)
    check_cursor_frontmatter(errors)
    check_content_files(errors)
    check_guideline_sections(errors)
    check_canonical_sync(errors)
    check_forbidden_wording(errors)
    check_forbidden_phrases(errors)
    check_readme_disclaimers(errors)
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
