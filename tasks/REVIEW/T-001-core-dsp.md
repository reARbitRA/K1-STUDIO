---
id: T-001
title: Core DSP and channel strip
type: task
status: REVIEW
version: 1.0.0
owner: pair
created: '2026-11-09'
updated: '2026-11-09'
supersedes: []
depends_on: []
implements:
- SPEC-001
traces_to:
- docs/TECHNICAL SPECIFICATION & ARCHITECTURE DOCUMENT.MD
tags:
- k1-studio
- mvp
confidence: high
acs:
- AC-1
- AC-2
- AC-3
- AC-4
- AC-5
- AC-6
- AC-7
- AC-8
plan: PLAN-001
size: M
branch: arena/a68eb821-k1-studio
---

# T-001 — Core DSP and channel strip

## Goal
Implement [SPEC-001](../../specs/dsp/SPEC-001-core-dsp-and-channel-strip.md) AC-1 through AC-8 as one independently reviewable
module delivery. The human approved the specification in advance on 2026-11-09.
This REVIEW card records implementation submission; actual command results are in LEDGER.

## Actual implementation paths
`src/k1_studio/dsp/engine.py`, `src/k1_studio/dsp/filters.py`, `tests/dsp/test_core.py`

## Acceptance mapping
| AC | Required test name in tests/dsp/test_core.py |
| --- | --- |
| AC-1 | test_ac_1_canonical_audio |
| AC-2 | test_ac_2_gain_phase_validation |
| AC-3 | test_ac_3_equal_power_pan |
| AC-4 | test_ac_4_mute_solo_padding |
| AC-5 | test_ac_5_headroom |
| AC-6 | test_ac_6_channel_eq |
| AC-7 | test_ac_7_channel_compression |
| AC-8 | test_ac_8_order_and_immutability |

All listed ACs are in scope. Expected file names may be refined without changing the
behavioral contract; update actual TRACE paths once created. No fake files/test stubs
should be added just to satisfy metadata checks.

## Steps
1. Install/pin product/test dependencies in isolated development configuration; add a
   real product test target to `make test` without dropping the forge tests.
2. Write every mapped test red; implement canonicalization and isolated controls.
3. Implement channel filters/compression, pan, solo/mute summation and safety scaling.
4. Inject region/master callbacks for order tests; do not implement future DSP modules.
5. Verify, record actual versions/results, update actual file traces and request review.

## Verification
`.venv/bin/python -m pytest tests/dsp/test_core.py -v`
Then `make verify` (including wired-in product tests), product lint/typecheck and
`make secret-scan` with gitleaks installed. Product commands now execute in this checkout; see LEDGER for results. Paste actual output/exit codes into the PR.

## Out of scope
Region/master implementation, HTTP/UI, separation and changing spec defaults.

## Notes / blockers
First builder task; no product dependency is installed yet.
Size M is a delivery estimate, not a claim of completed effort. If actual scope exceeds
one session or loses atomic reviewability, stop and propose a plan/task split for human
approval before broadening work; do not silently create more IDs or skip ACs.
Spec §9 contains delegated choices/limitations that must remain explicit. DONE follows
quality/DOD.md; do not inherit T-FORGE-001's one-time human completion exception.

## Builder handoff — 2026-11-09
Implemented on the assigned branch and submitted to REVIEW, not self-approved DONE.
See `.forge/LEDGER.md` for executed checks and remaining sign-off obligations.
Original planned paths above are refined to actual source-root locations per the human
requirement that all production code reside under src/. No spec behavior was rewritten.
