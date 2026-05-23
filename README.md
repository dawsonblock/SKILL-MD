# Karpathy-Inspired Coding Agent Guidelines

<p align="center">
  <strong>A practical instruction pack that makes coding agents more reliable, simpler, and less destructive.</strong>
</p>

<p align="center">
  <a href="./README.md">English</a> · <a href="./README.zh.md">简体中文</a>
</p>

<p align="center">
  <img alt="Version" src="https://img.shields.io/badge/version-1.1.1-2563eb">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-16a34a">
  <img alt="Validation" src="https://img.shields.io/badge/validation-required-f59e0b">
</p>

> Not affiliated with or endorsed by Andrej Karpathy.

A small instruction pack for coding agents, inspired by public observations from Andrej Karpathy about LLM coding pitfalls. This project is not affiliated with or endorsed by Andrej Karpathy.

## Why This Exists

Most coding agents fail in the same predictable ways:

- They make silent assumptions.
- They overengineer straightforward tasks.
- They modify unrelated code while fixing one issue.
- They execute without clear, testable success criteria.

This repo gives you one coherent fix: a concise behavior contract plus tooling that keeps every distribution format in sync.

## The 4 Principles

| Principle | Prevents |
| --- | --- |
| Think Before Coding | Silent assumptions, hidden confusion, missing tradeoffs |
| Simplicity First | Premature abstraction, bloated implementations |
| Surgical Changes | Drive-by edits, style drift, unrelated refactors |
| Goal-Driven Execution | Vague implementation without verification |

## Install

### Option A: Claude Code Plugin (recommended)

Add marketplace:

```bash
/plugin marketplace add forrestchang/andrej-karpathy-skills
```

Install plugin:

```bash
/plugin install andrej-karpathy-skills@karpathy-skills
```

### Option B: CLAUDE.md (per project)

New project:

```bash
curl -o CLAUDE.md https://raw.githubusercontent.com/forrestchang/andrej-karpathy-skills/main/CLAUDE.md
```

Existing project (append):

```bash
echo "" >> CLAUDE.md
curl https://raw.githubusercontent.com/forrestchang/andrej-karpathy-skills/main/CLAUDE.md >> CLAUDE.md
```

## Cursor Support

This repository ships a committed Cursor project rule at [.cursor/rules/karpathy-guidelines.mdc](.cursor/rules/karpathy-guidelines.mdc), so the guidelines apply automatically when opened in Cursor.

See [CURSOR.md](CURSOR.md) for setup and contributor workflow.

## Canonical Source and Sync Model

To prevent drift across files, guideline content is centralized and generated:

- Canonical content: [docs/guidelines.md](docs/guidelines.md)
- Generator: [scripts/sync_guidelines.py](scripts/sync_guidelines.py)
- Validator: [scripts/validate.py](scripts/validate.py)

Generated targets:

- [CLAUDE.md](CLAUDE.md)
- [.cursor/rules/karpathy-guidelines.mdc](.cursor/rules/karpathy-guidelines.mdc)
- [.github/copilot-instructions.md](.github/copilot-instructions.md)
- [skills/karpathy-guidelines/SKILL.md](skills/karpathy-guidelines/SKILL.md)

## Using with VS Code Copilot

This repository includes Copilot custom instructions at:

```text
.github/copilot-instructions.md
```

VS Code and GitHub Copilot use this file as repository-level guidance for chat and coding tasks. It is generated from [docs/guidelines.md](docs/guidelines.md); do not edit it directly.

After changing the canonical guideline file, run:

```bash
python3 scripts/check.py
```

Optional reusable prompt files live in:

```text
.github/prompts/repo-repair.prompt.md
.github/prompts/verify-change.prompt.md
.github/prompts/surgical-edit.prompt.md
```

## Development

The canonical guideline body lives in:

```text
docs/guidelines.md
```

After editing it, regenerate derived files:

```bash
python3 scripts/sync_guidelines.py
```

Check sync and validation:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/sync_guidelines.py --check
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -p "test_*.py"
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate.py
```

Or run the full sequence with one command:

```bash
python3 scripts/check.py
```

Build and verify a release archive end-to-end:

```bash
python3 scripts/package_release.py
```

This creates `dist/SKILL-MD-main-fixed.zip`, extracts it to a temporary directory, and reruns `scripts/check.py` against the extracted copy.

Run validation before committing:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate.py
```

`PYTHONDONTWRITEBYTECODE=1` prevents Python from creating `__pycache__` and `.pyc` files, which are intentionally rejected by repository validation.

This checks plugin JSON, Cursor frontmatter, required guideline sections, canonical body sync, and forbidden outdated wording/patterns.

The generated files are:

- `CLAUDE.md`
- `.cursor/rules/karpathy-guidelines.mdc`
- `.github/copilot-instructions.md`
- `skills/karpathy-guidelines/SKILL.md`

## What Good Looks Like

A healthy setup typically produces:

- Smaller, cleaner diffs with fewer unrelated edits
- Fewer overengineered rewrites
- Clarifying questions before implementation
- Stronger test-and-verify loops for non-trivial tasks

For concrete before/after examples, see [EXAMPLES.md](EXAMPLES.md).

## Repository Layout

```text
.
├── CLAUDE.md
├── CURSOR.md
├── EXAMPLES.md
├── README.md
├── README.zh.md
├── docs/
│   └── guidelines.md
├── scripts/
│   ├── check.py
│   ├── package_release.py
│   ├── sync_guidelines.py
│   └── validate.py
├── skills/
│   └── karpathy-guidelines/
│       └── SKILL.md
├── .claude-plugin/
│   ├── marketplace.json
│   └── plugin.json
└── .github/
  ├── copilot-instructions.md
  ├── prompts/
  │   ├── repo-repair.prompt.md
  │   ├── verify-change.prompt.md
  │   └── surgical-edit.prompt.md
    └── workflows/
        └── validate.yml
```

## License

MIT — see [LICENSE](LICENSE).
