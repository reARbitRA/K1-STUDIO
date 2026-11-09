---
id: FORGE-SPEC-INDEX
title: Specification index
type: index
status: ACTIVE
version: 1.1.0
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
---

# Specification index

## Human authorization
On 2026-11-09 the owner explicitly approved SPEC-001–SPEC-004 in advance and delegated
formalization to the ARCHITECT. All four contracts below are now IMPLEMENTING, with code/tests submitted for review;
none is human VERIFIED. PLAN-001 remains ACTIVE; T-001–T-004 are REVIEW.
The source architecture remains unchanged and hash-pinned as provenance, not a fifth spec.

| Spec | Title | Status | Plan | Task | ACs |
| --- | --- | --- | --- | --- | --- |
| [SPEC-001](dsp/SPEC-001-core-dsp-and-channel-strip.md) | Core DSP, mixer and channel strip | IMPLEMENTING | PLAN-001 | T-001 | AC-1–AC-8 |
| [SPEC-002](dsp/SPEC-002-surgical-region-fx.md) | Surgical region FX / six presets | IMPLEMENTING | PLAN-001 | T-002 | AC-1–AC-10 |
| [SPEC-003](dsp/SPEC-003-analog-master-bus.md) | Analog master bus / WAV | IMPLEMENTING | PLAN-001 | T-003 | AC-1–AC-9 |
| [SPEC-004](app/SPEC-004-api-and-frontend-ui.md) | API, Demucs and dark-studio UI | IMPLEMENTING | PLAN-001 | T-004 | AC-1–AC-12 |

## Dependency order
SPEC-001 → SPEC-002 → SPEC-003 → SPEC-004. Detailed source provenance, delegated
choices, source limitations, exact rules and planned verification mappings live in each
spec. Approved content is frozen after this formalization session; future changes require
a DRAFT revision or proposed ADR per AGENTS.md. Do not infer executed AC coverage from
successful forge-lint: named tests for all 39 product ACs now exist, but perceptual/model/full operational
sign-off remains outstanding. See LEDGER for actual executed results and limitations.
