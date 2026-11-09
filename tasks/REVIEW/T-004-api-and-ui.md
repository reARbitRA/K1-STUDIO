---
id: T-004
title: Local API, Demucs and workstation UI
type: task
status: REVIEW
version: 1.0.0
owner: pair
created: '2026-11-09'
updated: '2026-11-09'
supersedes: []
depends_on:
- T-003
implements:
- SPEC-004
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
- AC-11
- AC-12
plan: PLAN-001
size: M
branch: arena/a68eb821-k1-studio
---

# T-004 — Local API, Demucs and workstation UI

## Goal
Implement [SPEC-004](../../specs/app/SPEC-004-api-and-frontend-ui.md) AC-1 through AC-12 as one independently reviewable
module delivery. The human approved the specification in advance on 2026-11-09.
This REVIEW card records implementation submission; actual command results are in LEDGER.

## Actual implementation paths
`src/k1_studio/app/main.py`, `src/k1_studio/app/schemas.py`, `src/k1_studio/app/service.py`, `src/k1_studio/app/admission.py`, `src/k1_studio/dsp/separator.py`, `src/frontend/App.tsx`, `src/frontend/Wave.tsx`, `src/frontend/store.ts`, `src/frontend/audio.ts`, `tests/app/test_api.py`, `tests/frontend/store.test.ts`, `tests/frontend/e2e/studio.spec.ts`

## Acceptance mapping
| AC | Required test name | Planned file |
| --- | --- | --- |
| AC-1 | test_ac_1_project_schema | tests/app/test_api.py |
| AC-2 | test_ac_2_upload_and_peaks | tests/app/test_api.py |
| AC-3 | test_ac_3_demucs_modes | tests/app/test_api.py |
| AC-4 | test_ac_4_job_websocket | tests/app/test_api.py |
| AC-5 | test_ac_5_preview_slice | tests/app/test_api.py |
| AC-6 | test_ac_6_render_downloads | tests/app/test_api.py |
| AC-7 | test_ac_7_security_limits | tests/app/test_api.py |
| AC-8 | test_ac_8_history_persistence | tests/frontend/store.test.ts |
| AC-9 | test_ac_9_desktop_layout | tests/frontend/e2e/studio.spec.ts |
| AC-10 | test_ac_10_transport_regions | tests/frontend/e2e/studio.spec.ts |
| AC-11 | test_ac_11_accessibility_errors | tests/frontend/e2e/studio.spec.ts |
| AC-12 | test_ac_12_preview_latency | tests/app/test_api.py |

All listed ACs are in scope. Expected file names may be refined without changing the
behavioral contract; update actual TRACE paths once created. No fake files/test stubs
should be added just to satisfy metadata checks.

## Steps
1. Add typed API schemas, workspace asset resolver and fake-worker integration tests.
2. Implement upload/peaks, Demucs adapter, job admission/WS, preview and render/download.
3. Add React/TypeScript/Vite frontend with WaveSurfer v7 and Zustand transaction history;
   implement all four zones, numeric/keyboard controls and relative proxy routes.
4. Add Vitest/Playwright/benchmark commands and product lint/typecheck; extend the
   source-root trace gate to frontend/src before adding frontend runtime code, with
   regression tests (do not leave that subtree outside governance checks).
5. Provide documented native/compose startup and opt-in real-model smoke instructions;
   run full API/UI/latency suite, preserve failure evidence and request independent review.

## Verification
`.venv/bin/python -m pytest tests/app/test_api.py -v`
`npm --prefix src/frontend run test -- --run`
`npm --prefix src/frontend run test:e2e`
`npm --prefix src/frontend run lint && npm --prefix src/frontend run typecheck`
Then `make verify` (including wired-in product tests), product lint/typecheck and
`make secret-scan` with gitleaks installed. Product commands now execute in this checkout; see LEDGER for results. Paste actual output/exit codes into the PR.

## Out of scope
New DSP behavior, authentication/cloud hosting, collaboration, arbitrary uploads/code execution.

## Notes / blockers
Depends on T-003 reviewed integration output; do not duplicate that implementation.
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

Pending: real Demucs/weights smoke, qualifying ≥4-core/8-GiB benchmark, full manual keyboard/audio acceptance and container smoke. This sandbox has 2 cores/~4 GiB; measured warm-cache latency is supplemental only.
