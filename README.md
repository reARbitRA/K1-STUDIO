---
id: FORGE-README
title: K1-STUDIO repository
type: knowledge
status: ACTIVE
version: 1.1.0
owner: agent
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

# K1-STUDIO

A local-first surgical stem-mixing and mastering workstation: float32 / 48 kHz DSP,
six non-destructive region presets, an analog-style master chain, and a single-screen
React studio. Production code lives entirely under `src/`. Four implementation tasks
are in REVIEW; the specs are IMPLEMENTING, not human VERIFIED.

## Start locally
Requires Python 3.11+, Node 22+, npm, make, Linux/macOS native audio dependencies.
```sh
make bootstrap
# Terminal 1 (loopback-only by default):
PYTHONPATH=src .venv/bin/uvicorn k1_studio.app.main:app --port 8000
# Terminal 2:
npm --prefix src/frontend run dev -- --port 5173
```
Open http://localhost:5173. Import WAV/FLAC/AIFF, or choose **Try demo** to generate four
real synthetic WAV files and send them through the real upload API. Nothing is sent to
an external audio service. Select a time interval, choose a preset, audition, adjust
master controls, and export a verified PCM_24 WAV. Export presents a download link.

Basic transport uses Web Audio gain/pan/mute/solo/phase and meters. **Preview region**
is the authoritative Python FX/master render. A/B is audition-only, never export bypass.
No licensed hardware-emulation fidelity is claimed. See spec §9 for DSP limitations.

## Checks
```sh
make verify                    # pytest + store test, Ruff/ESLint, mypy/tsc, forge-lint
make build test-e2e             # build + real Chromium browser tests
make forge-lint BASE=cdfb576f0e875353f3b10e62badb21acf6d58ae3
make secret-scan                # separately installed gitleaks 8.24.2 required
PYTHONPATH=src .venv/bin/python tests/generate_boundary_evidence.py
```
Browser tests start their own API/Vite servers when ports are free, or reuse local
servers outside CI. Chromium and test-only native libraries come from a pinned npm
package; no browser release download is needed. Evidence/caches/audio are ignored.

## Separation and containers
Demucs inference is optional: install `requirements-separation.txt`, provision weights
locally with appropriate provenance/license, and set `K1_DEMUCS_MODELS` to the repository
of local model weights. Missing weights return 503; **no hidden model downloads** occur.
Tests inject deterministic fake component buffers; real-model quality is not validated.
`docker compose up --build` is provided for local port 8080; Docker was unavailable in
this sandbox, so the container path is **not tested**. See ops/DEPLOY.md.

## State, governance and limitations
- Agents start with [AGENTS.md](AGENTS.md); humans inspect [.forge/STATE.md](.forge/STATE.md),
  [PLAN-001](plans/PLAN-001-k1-studio-mvp.md) and [specs/INDEX.md](specs/INDEX.md).
- The [original architecture](docs/TECHNICAL%20SPECIFICATION%20%26%20ARCHITECTURE%20DOCUMENT.MD)
  is unchanged; its exact-path/hash frontmatter exception remains scoped to that file.
- No authentication/multitenancy: keep services local/private. Preview proxies use
  relative browser URLs, explicit origin/host checks, and no wildcard backend CORS.
- Server registries/jobs are process-local; browser JSON survives reload while the server
  runs. Restarting the server loses issued handles/jobs; persistent workspace recovery
  needs further review. Original files remain on disk for manual recovery, not auto-loaded.
- Listening sign-off, real Demucs smoke, qualifying-hardware benchmark, Docker and secret
  scan remain outstanding. Current warm-cache performance is not cold-render evidence.
- GitHub required checks/CODEOWNERS and any PR are maintainer follow-ups. No secrets,
  models, large fixtures, commits, or pushes were added by this builder session.
