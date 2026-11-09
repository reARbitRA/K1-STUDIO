---
id: PLAN-001
title: K1-STUDIO MVP delivery plan
type: plan
status: ACTIVE
version: 1.0.0
owner: pair
created: '2026-11-09'
updated: '2026-11-09'
supersedes: []
depends_on:
- SPEC-001
- SPEC-002
- SPEC-003
- SPEC-004
implements:
- SPEC-001
- SPEC-002
- SPEC-003
- SPEC-004
traces_to:
- docs/TECHNICAL SPECIFICATION & ARCHITECTURE DOCUMENT.MD
tags:
- k1-studio
- mvp
confidence: high
---

# PLAN-001 — K1-STUDIO MVP

## Authorization and goal
ACTIVE under the human's explicit 2026-11-09 control-plane instruction. Implement the
four APPROVED specifications as ordered, reviewable module deliveries; implementation has been submitted as four REVIEW tasks, not human-verified delivery. Product source is rooted in src/k1_studio rather than the legacy backend/app
sketch so Python code is covered by the existing root-src trace gate. The current human builder instruction places the frontend in src/frontend too, so
the existing root-src trace gate covers both runtimes; tests live in tests/frontend.

## Inputs and contract precedence
SPEC-001–SPEC-004 are the behavioral contracts. The untouched original architecture is
provenance; if prose disagrees, the explicit formalization notes in spec §9 govern MVP
behavior. New business choices need a DRAFT revision/proposed ADR; no silent drift.
T-FORGE-001 is human-completed by a scoped override, not precedent to bypass DoD.

## Ordered work / acceptance coverage
| Order | Task | Spec | All acceptance criteria | Dependency | Size |
| --- | --- | --- | --- | --- | --- |
| 1 | T-001 | SPEC-001 | AC-1–AC-8 (8) | None | M |
| 2 | T-002 | SPEC-002 | AC-1–AC-10 (10) | T-001 | M |
| 3 | T-003 | SPEC-003 | AC-1–AC-9 (9) | T-002 | M |
| 4 | T-004 | SPEC-004 | AC-1–AC-12 (12) | T-003 | M |

Total: 39 numbered ACs, each assigned once to its corresponding task. The detailed
AC→test-name→planned-path mappings are in each spec §10 and matching task card.
The four requested cards are coherent module-level delivery units, not proof that all
four fit one session. T-004 is the largest risk; if any is actually L, propose human-
approved smaller cards before building rather than misrepresenting it as atomic work.

## Integration order and boundaries
1. T-001 establishes canonical buffers, DSP dependency versions, pytest and a combined
   methodology/product test target. Use injected callbacks to test future-stage order.
2. T-002 installs region processing at the approved track/bus positions. Use synthetic,
   versioned/provenanced fixtures; retain audition artifacts outside Git when large.
3. T-003 accepts the pre-master sum and exports independently checked files. Test meters
   must not merely repeat a limiter's self-reported telemetry.
4. T-004 consumes the same project graph and backend DSP. Fake-model tests run in ordinary
   CI; real models/weights need explicit local provisioning, provenance and separate smoke
   evidence. Frontend does not claim to emulate offline analog mastering in Web Audio.

## Verification / definition of done
Each task runs its exact product commands and the existing methodology checks. Extend
`make test`/CI with genuine product coverage; current 42 forge tests do not satisfy any
product AC. Never mark a spec IMPLEMENTED until every mapped test actually executes and
passes; then populate TRACE with real test paths and execution evidence. Humans alone
mark VERIFIED after deployed acceptance, including click-free listening, true-peak/LUFS,
model smoke and UI journeys. Run secret-scan before claiming a fully green baseline.

## Risks and required honesty
- Finite-order side filtering is not an exact sub-85 Hz brickwall: SPEC-003 §9 preserves
  filter behavior and documents the limited calibration sign-off instead of a false proof.
- Infeasible loudness/ceiling combinations must fail, not publish noncompliant WAVs.
- Preview latency is measured on the explicit SPEC-004 workload; no “<300ms” claim yet.
- Four large functional areas may exceed the original M estimates; split transparently.
- Python/native DSP/model dependencies, browser audio timing and downloaded weights are
  untested. No product runtime/deployment exists in this documentation session.
- Gitleaks is unavailable locally; prior sandbox egress prevented the official binary.

## Rollback
Original architecture is unchanged. Revert only a failed module delivery on this branch
when authorized; preserve ADR/ledger history. Render failures must not mutate project
state or source assets; publication of output files is atomic. No destructive DB migration
or external infrastructure operation is part of this plan.

## Exit criteria
Four reviewed DONE tasks, 39 ACs with executed passing tests, product plus methodology
checks wired into CI, actual trace/evidence links, complete env/runbooks, verified exports,
and human product verification. Current progress: 4/4 tasks submitted to REVIEW, 0/4 independently DONE.
