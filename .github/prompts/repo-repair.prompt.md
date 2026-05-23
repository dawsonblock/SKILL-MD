---
name: repo-repair
description: Inspect a repository, identify blockers, make minimal repairs, and verify results.
---
Map the repository first. Identify entrypoints, dependency files, test commands, build/run commands, and broken files.
Separate facts from assumptions. Fix blockers first. Keep patches small. Do not invent architecture.
End with:
- files changed
- commands run
- verification results
- remaining failures
