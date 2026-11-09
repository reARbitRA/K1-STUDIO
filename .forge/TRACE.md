---
id: "FORGE-TRACE"
title: "Traceability matrix"
type: "trace"
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

# Traceability matrix

Use one row per spec; list exact source/test paths in backticks. A header reference may
trace source files, but IMPLEMENTED/VERIFIED acceptance tests must be listed here by spec.
The linter checks structural links; it cannot prove behavior, execution, or human approval.

| Spec | Plan | Task | Source files | Test files | Branch | Commit / PR / evidence |
| --- | --- | --- | --- | --- | --- | --- |
| Methodology (no product spec) | — | T-FORGE-001 | `scripts/forge_lint.py` | `tests/forge/test_forge_lint.py` | arena/a68eb821-k1-studio | Local checks recorded in `.forge/LEDGER.md`; no PR yet |
| Bootstrap and tooling (no product spec) | — | T-FORGE-001 | `Makefile`, `requirements-dev.txt`, `pyproject.toml`, `.gitignore`, `scripts/__init__.py`, `.forge/config.json` | `tests/forge/test_forge_lint.py` | arena/a68eb821-k1-studio | Working tree; verification in LEDGER |
| Governance (no product spec) | — | T-FORGE-001 | `AGENTS.md`, `README.md`, `.forge/STATE.md`, `.forge/LEDGER.md`, `.forge/CONVENTIONS.md`, `.forge/GLOSSARY.md`, `.forge/TRACE.md`, `specs/INDEX.md`, `tasks/DONE/T-FORGE-001-scaffold.md` | `scripts/forge_lint.py` (metadata check) | arena/a68eb821-k1-studio | Human completion override 2026-11-09; no PR exists |
| Quality and operations (no product spec) | — | T-FORGE-001 | `quality/DOD.md`, `quality/TEST-STRATEGY.md`, `quality/SECURITY-BASELINE.md`, `ops/ENV.md`, `ops/DEPLOY.md`, `ops/KEYS.md`, `ops/RUNBOOK.md`, `.github/workflows/quality.yml`, `.github/PULL_REQUEST_TEMPLATE.md` | CI configured; not run | arena/a68eb821-k1-studio | Local secret scan unavailable; see LEDGER |
| Templates (no product spec) | — | T-FORGE-001 | `.forge/templates/spec.md`, `.forge/templates/plan.md`, `.forge/templates/task.md`, `.forge/templates/adr.md`, `.forge/templates/brainstorm.md`, `.forge/templates/vision.md`, `.forge/templates/knowledge.md`, `.forge/templates/quality.md`, `.forge/templates/ops.md`, `.forge/templates/state.md`, `.forge/templates/ledger.md`, `.forge/templates/trace.md` | `scripts/forge_lint.py` (metadata check) | arena/a68eb821-k1-studio | Working tree; no product specification implied |


## Product implementation trace — T-001 through T-004

All paths below exist. Specs remain IMPLEMENTING pending independent review and the
outstanding perceptual/model/operational evidence, not human VERIFIED. Test-name matching
is structural; execution results and limitations are recorded in LEDGER.

| Spec | Plan | Task | Source files | Test files | Branch | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| SPEC-001 | PLAN-001 | T-001 | `src/k1_studio/__init__.py`, `src/k1_studio/app/service.py`, `src/k1_studio/dsp/__init__.py`, `src/k1_studio/dsp/engine.py`, `src/k1_studio/dsp/filters.py` | `tests/dsp/test_core.py` | arena/a68eb821-k1-studio | Automated results in LEDGER; independent review pending |
| SPEC-002 | PLAN-001 | T-002 | `src/k1_studio/app/service.py`, `src/k1_studio/dsp/filters.py`, `src/k1_studio/dsp/presets.py`, `src/k1_studio/dsp/regions.py` | `tests/dsp/test_regions.py`, `tests/generate_boundary_evidence.py` | arena/a68eb821-k1-studio | Automated results in LEDGER; independent review pending |
| SPEC-003 | PLAN-001 | T-003 | `src/k1_studio/app/service.py`, `src/k1_studio/dsp/filters.py`, `src/k1_studio/dsp/mastering.py` | `tests/dsp/test_mastering.py` | arena/a68eb821-k1-studio | Automated results in LEDGER; independent review pending |
| SPEC-004 | PLAN-001 | T-004 | `src/Dockerfile.api`, `src/frontend/App.tsx`, `src/frontend/Dockerfile`, `src/frontend/Wave.tsx`, `src/frontend/audio.ts`, `src/frontend/index.html`, `src/frontend/main.tsx`, `src/frontend/nginx.conf`, `src/frontend/playwright.config.ts`, `src/frontend/postcss.config.js`, `src/frontend/store.ts`, `src/frontend/studio.css`, `src/frontend/tailwind.config.js`, `src/frontend/vite.config.ts`, `src/frontend/vitest.config.ts`, `src/k1_studio/app/__init__.py`, `src/k1_studio/app/admission.py`, `src/k1_studio/app/main.py`, `src/k1_studio/app/schemas.py`, `src/k1_studio/app/service.py`, `src/k1_studio/dsp/separator.py`, `src/frontend/package.json`, `src/frontend/tsconfig.json` | `tests/app/test_api.py`, `tests/frontend/store.test.ts`, `tests/frontend/e2e/studio.spec.ts` | arena/a68eb821-k1-studio | Automated results in LEDGER; independent review pending |

Infrastructure updated with the implementation: `Makefile`, `pyproject.toml`,
`requirements.txt`, `requirements-dev.txt`, `requirements-separation.txt`, `package.json`,
`package-lock.json`, `eslint.config.js`, `.gitignore`, `.dockerignore`, `docker-compose.yml`,
and `.github/workflows/quality.yml`. No product source exists outside src/.
No commits/PRs exist yet. Docker, real model inference, human listening and secret scanning
are not validated by the passing automated checks. All source originals remain unchanged.
