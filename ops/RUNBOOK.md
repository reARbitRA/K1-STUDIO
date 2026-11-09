---
id: FORGE-RUNBOOK
title: Methodology operations runbook
type: ops
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

# Runbook

## Agent / local bootstrap
Read AGENTS.md. `make bootstrap && make verify` installs Python/npm dependencies and runs
both governance and product checks. `make build test-e2e` builds and runs Chromium; CI
has a browser job. `make secret-scan` requires separately provisioned gitleaks 8.24.2.
Missing tools and unexecuted CI are not green evidence.

## API and workflow diagnostics
- 503 model_unavailable: provision Demucs/runtime and weights explicitly; no auto-download.
- 409 busy: wait for the one heavy job; no unbounded worker queue.
- 409 loudness_target_unreachable: requested LUFS and ceiling could not both be verified;
  do not change peak limits silently or publish a partial file.
- 404 asset/project after restart: registry is process-local; re-import audio. Files remain
  on disk; do not delete them. Browser JSON alone cannot rebuild server handles yet.
- Invalid upload: raw multipart storage is bounded before decode; encoded audio is limited
  to 256 MiB and decoded duration to 30 minutes. Formats: WAV/FLAC/AIFF, mono/stereo only.
- UI transport is basic Web Audio; use authoritative Preview region for FX/master sound.
- Native browser libraries are generated under ignored .verification; rerun bootstrap and
  test-e2e rather than committing binaries. Tests use real local API unless explicitly mocked.

## Governance failures
Metadata/trace/date errors must be corrected, not hidden with broad exemptions. Supply
the real PR BASE for append-only ledger enforcement. Original architecture is hash-pinned.
Keep tasks in REVIEW until independent review and DoD evidence exist; no self-verification.
Main branch protection and known human CODEOWNERS remain owner configuration tasks.

## Boundary evidence
`PYTHONPATH=src .venv/bin/python tests/generate_boundary_evidence.py` regenerates six
synthetic WAV/spectrogram/data sets in .verification/boundaries. Listen and inspect; the
script does not record a human no-click verdict. Keep large/generated artifacts out of Git.
