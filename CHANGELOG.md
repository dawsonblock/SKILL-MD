# Changelog

## 1.1.1

- Quoted generated YAML frontmatter descriptions.
- Added validation for frontmatter description quoting.
- Fixed stale Chinese README guidance.
- Added Chinese stale wording checks.
- Added cache/junk file validation.
- Removed compiled Python cache files from release archives.
- Expanded tests for validation failure modes.
- Fixed README version badge mismatch.
- Added validation for README badge/version consistency.
- Updated CI to disable Python bytecode generation.
- Re-runs validation after unit tests in CI.
- Documented bytecode-safe local validation commands.
- Added `scripts/check.py` one-command local verification runner.
- Updated `scripts/check.py` to clean existing junk artifacts before validation and before final post-test validation.
- Added `scripts/package_release.py` for reproducible release archive build + extracted-copy verification.
- Made `scripts/sync_guidelines.py` create missing target parent directories before writing generated files.
- Softened remaining clarification wording to avoid unnecessary stops.

## 1.1.0

- Added canonical `docs/guidelines.md`.
- Added sync script for generated guideline files.
- Added validation script and GitHub Actions workflow.
- Added verification discipline.
- Added repo repair protocol.
- Added claim boundaries.
- Added task modes.
- Added output discipline.
- Replaced over-broad clarification wording.
- Replaced unsafe “impossible scenario” error-handling wording.
- Cleaned attribution language.
- Corrected examples for rate limiting, logging, and deterministic sorting.

## 1.0.0

- Initial guideline pack.
