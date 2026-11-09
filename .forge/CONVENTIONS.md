---
id: "FORGE-CONVENTIONS"
title: "Repository conventions"
type: "governance"
status: "ACTIVE"
version: "1.0.0"
owner: "agent"
created: "2026-11-09"
updated: "2026-11-09"
supersedes: []
depends_on: []
implements: []
traces_to: []
tags: ["forge"]
confidence: "high"
---

# Conventions

## Naming and metadata
Use SPEC-001, PLAN-001, T-001, ADR-0001 identifiers for future product work. Methodology
records use FORGE-* and T-FORGE-* IDs. IDs are globally unique, including templates.
All Markdown, case-insensitive `.md`, outside `src/` requires YAML frontmatter with
id, title, type, status, version, owner, created, updated, supersedes, depends_on,
implements, traces_to, tags, confidence. Dates are UTC ISO dates; update on material edits.
Lists are YAML lists; version is semver. Templates use TEMPLATE-* IDs and type template.

Additional types: governance, ledger, state, glossary, trace, index, template. Their
states are DRAFT, ACTIVE, ARCHIVED. Vision/knowledge/ops/quality use these states too.
Product lifecycle states follow the templates and AGENTS.md; BLOCKED tasks reside in REVIEW.
Folder and task status must agree; a blocked task has a written BLOCKED explanation.
Human approval gates are policy/review controls, not something a status string proves.

## Code, tests, and traces
Python tooling: Python 3.11+, Ruff, strict mypy, unittest; dependencies pinned in
requirements-dev.txt; runtime pins are in requirements.txt. Infrastructure under scripts/
and tests/forge/ traces to T-FORGE-001; product integration tooling also traces to T-004.
All runtime Python and React code is under src/ per the builder's human instruction.
Frontend workspace: src/frontend; frontend tests: tests/frontend. Use `make verify` and
`make build test-e2e`; TypeScript headers use `// # SPEC-004`, CSS/HTML equivalent comments,
and JSON configs require explicit TRACE paths because comments are invalid JSON.
Every regular file beneath src/ must reference a real spec in a comment/header within
its first 20 lines, or an explicit path row in `.forge/TRACE.md`. Binary files use rows.
Use `# SPEC-001`, `// SPEC-001`, `/* SPEC-001 */`, or `<!-- SPEC-001 -->` as appropriate.
Product spec contracts use numbered AC-n criteria; tests use `test_ac_<n>_<slug>` in files
explicitly listed on the spec's TRACE row. AC IDs are local to a spec, not global.
A TRACE row uses exact repo-relative file paths in backticks; no globs or directories.

## Git and evidence
Commit format: `<type>(<scope>): <summary> [<TASK-ID>] [<SPEC-ID>]`.
Types: feat, fix, test, docs, refactor, chore, spec, adr. Omit SPEC-ID for tooling-only work.
Keep Arena's assigned branch; no automatic branch creation or credential setup.
Verification output lives in PRs; record command, result, date, and limits in the ledger.
Do not check in caches, downloaded binaries, or large audio fixtures.
