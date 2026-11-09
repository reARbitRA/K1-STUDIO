---
id: FORGE-AC-EVIDENCE
title: MVP acceptance evidence and review limits
type: quality
status: ACTIVE
version: 1.0.0
owner: agent
created: '2026-11-09'
updated: '2026-11-09'
supersedes: []
depends_on: []
implements:
- SPEC-001
- SPEC-002
- SPEC-003
- SPEC-004
traces_to:
- tests/dsp/test_core.py
- tests/dsp/test_regions.py
- tests/dsp/test_mastering.py
- tests/app/test_api.py
- tests/frontend/store.test.ts
- tests/frontend/e2e/studio.spec.ts
tags:
- mvp
- verification
confidence: high
---

# MVP acceptance evidence — builder submission, not human verification

## Executed automated checks
- `make verify`: exit 0. Pytest 87 passed (42 governance + 45 DSP/API cases), Vitest
  1 passed, Ruff/ESLint clean, strict mypy (16 files) and TypeScript clean, forge-lint PASS.
- `make build test-e2e`: exit 0. Frontend production build succeeds; Chromium 3 passed.
- All 39 AC names are present in real traced test files; no skipped/xfail cases were added.
  Name coverage is not proof of exhaustive acceptance or human sign-off.
- Base-aware forge-lint and ledger prefix checks are recorded in the session ledger.
- Original architecture reference stays byte-identical; no audio/model binaries in Git.

| Spec / task | Executed automation | Outstanding independent review / verification |
| --- | --- | --- |
| SPEC-001 / T-001 | Canonical rates/channels, gain/phase/ranges, pan, solo/mute/padding, headroom, EQ, compressor slope, order/immutability | Review tests against every rule and real stems; no human VERIFIED status |
| SPEC-002 / T-002 | Boundaries/fades, six presets, deterministic overlap, synthetic click endpoints | Human listening + spectrogram verdict for AC-10; broader subjective sound-quality evidence |
| SPEC-003 / T-003 | M/S/calibration/counterexample, EQ/blend/tape, three LUFS targets, independently oversampled exported PCM, intersample limiting, short/silent/unreachable/atomic failures, 16/24-bit output | Independent audio review; no hardware-emulation fidelity claim |
| SPEC-004 / T-004 | Schemas, real local upload/peaks, injected separator math, WS replay/failure, crop/full-render comparison, range downloads, origin/path/upload admission, history, layout/controls/error browser journeys | Real Demucs weights/runtime smoke, expanded manual keyboard/transport/audio journeys, qualifying-hardware benchmark, Docker startup |

## Latency — supplemental, not qualifying certification
Four 10-second tracks, one 1-second radio region and all master stages, 20 warmups then
100 sequential requests: latest recorded median 4.78 ms / p95 5.53 ms / max 5.89 ms.
This intentionally exercises a bounded immutable-graph full-DSP-result cache. It is **not**
a cold-cache performance claim. Linux x86_64 / Python 3.11.2, 2 logical CPUs and
4,034,452 KiB RAM; this is below SPEC-004's ≥4-core/8-GiB benchmark precondition, so repeat
on qualifying hardware before claiming full AC-12 certification. Tests print platform,
CPU/memory and latency distribution; no timing threshold was removed or relaxed.

## Reproducible artifacts
`PYTHONPATH=src .venv/bin/python tests/generate_boundary_evidence.py` writes six WAV,
SVG spectrogram and NumPy data bundles to ignored `.verification/boundaries`. These are
synthetic test signals, not user audio. They do not encode a listening verdict.
Browser tests exercise the actual local API; only the intentional error-path test mocks
an export failure. Demucs integration tests inject component buffers and do not load models.

## Security / operational limits
`make secret-scan` cannot execute: gitleaks missing (make exit 2 / recipe 127). The prior
release-asset download was blocked by sandbox egress. CI scanning is configured, not run.
`npm audit --omit=dev` reported zero production JS findings; this is not a full security audit.
Docker is unavailable here. Server handle/job registries are process-local, so browser
reload works during a server session but server restart requires re-importing assets.
No public/multiuser deployment, durable queue, full coverage percentage, CI success,
PR, or human VERIFIED product status is claimed. All four tasks remain REVIEW.
