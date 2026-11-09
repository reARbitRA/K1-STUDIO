---
id: "FORGE-TEST-STRATEGY"
title: "Verification strategy"
type: "quality"
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

# Test strategy

## Current executable baseline
`make test` runs pytest across tests/ (governance plus DSP/API), then Vitest project-history
checks. `make lint` runs Ruff/ESLint; `make typecheck` runs strict mypy on Python production
and governance tooling plus TypeScript tsc. `make forge-lint` completes make verify.
`make build test-e2e` builds the frontend and runs real Chromium studio journeys.
`make secret-scan` uses separately installed gitleaks. Models/weights, human listening,
qualifying-hardware latency and Docker are not proved by these passing commands.

## Forge-lint contract
- Parse YAML safely; enforce required metadata, enums, unique IDs, semver, date order,
  future-date rejection, and real ID references (including dependency cycles).
- Validate task directory/status, implements/plan references and BLOCKED explanations;
  DOING updated more than 48h ago is stale (date-only updated means midnight UTC).
- Require all src files to link to existing product specs via comments or TRACE rows.
  Referenced specs must be APPROVED, IMPLEMENTING, IMPLEMENTED, or VERIFIED.
- IMPLEMENTED/VERIFIED specs require numbered ACs and matching Python-style named tests
  in spec-specific test files on their TRACE row; one spec's test cannot cover another.
- With `--base <sha>`, a change under src/ requires LEDGER to retain all old bytes and
  append nonempty content. CI passes the actual PR base SHA. Missing/invalid base fails.
- All tracked Markdown plus new, nonignored Markdown are checked, including uppercase
  extensions. The single legacy exemption is exact-path, reasoned, SHA-256 pinned,
  and must stay untouched. Templates are checked too; no generic docs exclusion.

Limits: structural name matching is not executed coverage; source provenance is not
semantic equivalence. Human review owns approval identity, immutable ADRs, scope, and
vision changes. No local default PR diff can be guessed: run BASE explicitly to check
ledger append rules; CI always supplies it for pull requests.

## Product strategy (proposal, not an approved requirement)
Before product implementation, draft/approve tests for deterministic DSP units,
API integration, and golden-audio fixtures with documented provenance. Suggested
pyramid by test count: 70% unit / 20% integration / 10% E2E. Suggested line floors:
70% product, 90% security-critical code. These are not currently enforced or measured.
Candidate E2E journeys: ingest → region edits → save/reload → export; separation failure
recovery; transport/undo/redo. Choose exact thresholds and audio tolerances in specs.
Flakes: capture initial failure, at most three diagnostic reruns, then quarantine with
an assigned task and deadline; never retry silently to claim a green acceptance test.
