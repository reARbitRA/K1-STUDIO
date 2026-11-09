---
id: T-FORGE-001
title: Scaffold SPEC-FORGE methodology
type: task
status: DONE
version: 1.0.0
owner: pair
created: '2026-11-09'
updated: '2026-11-09'
supersedes: []
depends_on: []
implements: []
traces_to: []
tags:
- forge
confidence: high
size: M
branch: arena/a68eb821-k1-studio
---

# T-FORGE-001 — Methodology scaffold

## Goal
Install the governance scaffold requested by the human (option 1). No product code,
product-spec decomposition, credentials, pushes, or settings changes are in scope.
Methodology infrastructure is not a product spec implementation.

## Files (expected)
AGENTS.md; .forge/; scripts/forge_lint.py; tests/forge/; .github/; quality/; ops/;
Makefile; requirements-dev.txt; README.md; ignored-environment and tooling config.

## Steps
1. Preserve original architecture; document an exact legacy migration exemption.
2. Add bootstrap, lifecycle, approval, trace, handoff, and document templates.
3. Add executable tooling with regression tests and CI quality gates.
4. Verify locally, record results, and request human review.

## Verification
`make bootstrap && make verify && make forge-lint BASE=cdfb576f0e875353f3b10e62badb21acf6d58ae3`
`make secret-scan` (requires gitleaks 8.24.2).

## Out of scope
Product implementation or spec approval; GitHub settings/CODEOWNERS ownership assignment;
key generation; commit/push/PR unless separately requested.

## Notes / blockers
DONE by explicit human control-plane override on 2026-11-09: “I approve T-FORGE-001 —
move it from tasks/REVIEW/ to tasks/DONE/.” This is a scoped completion exception to the
ordinary PR/secret-scan DoD, not evidence that a PR exists or gitleaks passed. The human
approved the scaffold; verification facts remain in LEDGER. No global DoD rule changes.
