#!/usr/bin/env python3
"""Generate guideline targets from docs/guidelines.md canonical content."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
CANONICAL_PATH = ROOT / "docs" / "guidelines.md"

BEGIN = "<!-- BEGIN CANONICAL BODY -->"
END = "<!-- END CANONICAL BODY -->"
DESCRIPTION = (
    "Karpathy-inspired behavioral guidelines for coding agents: clarify assumptions, "
    "keep changes simple, edit surgically, and verify before claiming completion."
)

TARGETS = {
    "CLAUDE.md": ROOT / "CLAUDE.md",
    ".cursor/rules/karpathy-guidelines.mdc": ROOT
    / ".cursor"
    / "rules"
    / "karpathy-guidelines.mdc",
    ".github/copilot-instructions.md": ROOT
    / ".github"
    / "copilot-instructions.md",
    "skills/karpathy-guidelines/SKILL.md": ROOT
    / "skills"
    / "karpathy-guidelines"
    / "SKILL.md",
}


def extract_canonical_body(text: str) -> str:
    if BEGIN not in text or END not in text:
        raise ValueError(f"Missing canonical body markers in {CANONICAL_PATH}")
    start = text.index(BEGIN) + len(BEGIN)
    end = text.find(END, start)
    if end == -1:
        raise ValueError(
            f"Missing canonical body end marker after begin marker in {CANONICAL_PATH}"
        )
    body = text[start:end].strip("\n")
    if not body:
        raise ValueError("Canonical body is empty")
    return body + "\n"


def render_claude(body: str) -> str:
    return (
        "# CLAUDE.md\n\n"
        "<!-- GENERATED: Run `python3 scripts/sync_guidelines.py` -->\n\n"
        f"{BEGIN}\n"
        f"{body}"
        f"{END}\n"
    )


def render_mdc(body: str) -> str:
    return (
        "---\n"
        f'description: "{DESCRIPTION}"\n'
        "alwaysApply: true\n"
        "---\n\n"
        "# Karpathy behavioral guidelines\n\n"
        "<!-- GENERATED: Run `python3 scripts/sync_guidelines.py` -->\n\n"
        f"{BEGIN}\n"
        f"{body}"
        f"{END}\n"
    )


def render_skill(body: str) -> str:
    return (
        "---\n"
        "name: karpathy-guidelines\n"
        f'description: "{DESCRIPTION}"\n'
        "license: MIT\n"
        "---\n\n"
        "# Karpathy Guidelines\n\n"
        "Karpathy-inspired behavioral guidelines for coding agents.\n\n"
        "<!-- GENERATED: Run `python3 scripts/sync_guidelines.py` -->\n\n"
        f"{BEGIN}\n"
        f"{body}"
        f"{END}\n"
    )


def render_copilot_instructions(body: str) -> str:
    return (
        "# Coding Agent Guidelines\n"
        "Use these rules when writing, reviewing, repairing, or refactoring code in this repository.\n"
        f"{BEGIN}\n"
        f"{body}"
        f"{END}\n"
    )


def render_targets(body: str) -> dict[str, str]:
    return {
        "CLAUDE.md": render_claude(body),
        ".cursor/rules/karpathy-guidelines.mdc": render_mdc(body),
        ".github/copilot-instructions.md": render_copilot_instructions(body),
        "skills/karpathy-guidelines/SKILL.md": render_skill(body),
    }


def main() -> int:
    check_only = "--check" in sys.argv

    canonical_text = CANONICAL_PATH.read_text(encoding="utf-8")
    body = extract_canonical_body(canonical_text)
    rendered = render_targets(body)

    changed = []
    for key, content in rendered.items():
        path = TARGETS[key]
        current = path.read_text(encoding="utf-8") if path.exists() else ""
        if current != content:
            changed.append(path)
            if not check_only:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")

    if changed:
        if check_only:
            print("Out of sync guideline targets:")
            for path in changed:
                print(f"- {path.relative_to(ROOT)}")
            print("Run: python3 scripts/sync_guidelines.py")
            return 1
        print("Updated guideline targets:")
        for path in changed:
            print(f"- {path.relative_to(ROOT)}")
    else:
        print("Guideline targets are already in sync.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
