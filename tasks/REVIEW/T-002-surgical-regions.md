---
id: T-002
title: Surgical region engine and six presets
type: task
status: REVIEW
version: 1.0.0
owner: pair
created: '2026-11-09'
updated: '2026-11-09'
supersedes: []
depends_on:
- T-001
implements:
- SPEC-002
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
- AC-9
- AC-10
plan: PLAN-001
size: M
branch: arena/a68eb821-k1-studio
---

# T-002 — Surgical region engine and six presets

## Goal
Implement [SPEC-002](../../specs/dsp/SPEC-002-surgical-region-fx.md) AC-1 through AC-10 as one independently reviewable
module delivery. The human approved the specification in advance on 2026-11-09.
This REVIEW card records implementation submission; actual command results are in LEDGER.

## Actual implementation paths
`src/k1_studio/dsp/regions.py`, `src/k1_studio/dsp/presets.py`, `tests/dsp/test_regions.py`, `tests/generate_boundary_evidence.py`

## Acceptance mapping
| AC | Required test name in tests/dsp/test_regions.py |
| --- | --- |
| AC-1 | test_ac_1_zero_crossing_boundaries |
| AC-2 | test_ac_2_complementary_fades |
| AC-3 | test_ac_3_hard_mute |
| AC-4 | test_ac_4_nasa_radio |
| AC-5 | test_ac_5_underwater |
| AC-6 | test_ac_6_tape_stop |
| AC-7 | test_ac_7_stutter_degrade |
| AC-8 | test_ac_8_sub_drop |
| AC-9 | test_ac_9_overlap_and_targets |
| AC-10 | test_ac_10_click_boundary_fixtures |

All listed ACs are in scope. Expected file names may be refined without changing the
behavioral contract; update actual TRACE paths once created. No fake files/test stubs
should be added just to satisfy metadata checks.

## Steps
1. Write boundary/fade tests red against SPEC-001 buffer contracts.
2. Implement deterministic zero-crossing/fallback/short-region logic and wet blending.
3. Implement all six allowlisted presets and ordering/master-target dispatch.
4. Run mapped tests; generate reproducible synthetic boundary waveform/spectrogram
   evidence and request the human listening check for AC-10.
5. Record actual paths/results and request independent review.

## Verification
`.venv/bin/python -m pytest tests/dsp/test_regions.py -v`
Then `make verify` (including wired-in product tests), product lint/typecheck and
`make secret-scan` with gitleaks installed. Product commands now execute in this checkout; see LEDGER for results. Paste actual output/exit codes into the PR.

## Out of scope
Track/channel strip changes, mastering topology, HTTP/UI and extra presets.

## Notes / blockers
Depends on T-001 reviewed integration output; do not duplicate that implementation.
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

Pending: human no-click audition/spectrogram sign-off for AC-10. Generated evidence is reproducible, not a listening verdict.
