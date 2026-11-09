---
id: T-003
title: Master bus, true peak and WAV export
type: task
status: REVIEW
version: 1.0.0
owner: pair
created: '2026-11-09'
updated: '2026-11-09'
supersedes: []
depends_on:
- T-002
implements:
- SPEC-003
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
plan: PLAN-001
size: M
branch: arena/a68eb821-k1-studio
---

# T-003 — Master bus, true peak and WAV export

## Goal
Implement [SPEC-003](../../specs/dsp/SPEC-003-analog-master-bus.md) AC-1 through AC-9 as one independently reviewable
module delivery. The human approved the specification in advance on 2026-11-09.
This REVIEW card records implementation submission; actual command results are in LEDGER.

## Actual implementation paths
`src/k1_studio/dsp/mastering.py`, `tests/dsp/test_mastering.py`

## Acceptance mapping
| AC | Required test name in tests/dsp/test_mastering.py |
| --- | --- |
| AC-1 | test_ac_1_ms_filter_and_width |
| AC-2 | test_ac_2_low_band_correlation |
| AC-3 | test_ac_3_master_eq |
| AC-4 | test_ac_4_parallel_compression |
| AC-5 | test_ac_5_asymmetric_tape |
| AC-6 | test_ac_6_lufs_true_peak_export |
| AC-7 | test_ac_7_silence_short_and_failure |
| AC-8 | test_ac_8_pcm_formats_and_dither |
| AC-9 | test_ac_9_order_bypass_and_telemetry |

All listed ACs are in scope. Expected file names may be refined without changing the
behavioral contract; update actual TRACE paths once created. No fake files/test stubs
should be added just to satisfy metadata checks.

## Steps
1. Write each stage's analytical tests and independent meter fixtures before DSP.
2. Implement M/S filtering/padding, EQ, parallel compression and tape in strict order.
3. Implement LUFS gain, oversampled lookahead limiting and decoded-PCM verification.
4. Add atomic 24-bit output and seeded 16-bit TPDF path; test silence/short/unreachable
   targets and cleanup. Preserve the documented finite-filter limitation.
5. Run mapped tests, record independent compliance evidence, update traces and review.

## Verification
`.venv/bin/python -m pytest tests/dsp/test_mastering.py -v`
Then `make verify` (including wired-in product tests), product lint/typecheck and
`make secret-scan` with gitleaks installed. Product commands now execute in this checkout; see LEDGER for results. Paste actual output/exit codes into the PR.

## Out of scope
Replacing the specified finite-order filter with a brickwall; API/UI or hardware-emulator claims.

## Notes / blockers
Depends on T-002 reviewed integration output; do not duplicate that implementation.
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
