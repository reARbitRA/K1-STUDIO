---
id: FORGE-DEPLOY
title: Deployment status
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

# Local deployment

## Native development (executed in Arena)
`make bootstrap`, then `PYTHONPATH=src .venv/bin/uvicorn k1_studio.app.main:app --port 8000`
and `npm --prefix src/frontend run dev -- --port 5173` in separate terminals. In Arena,
servers bind 0.0.0.0, frontend routes /api and /ws relatively, and host/origin checks permit
the preview host. Native API/UI and real browser tests executed; this is not public hosting.

## Container path (provided; not executed)
`docker compose up --build` builds src/Dockerfile.api and src/frontend/Dockerfile.
The unprivileged frontend serves on loopback host port 8080 and proxies API/WS to the
private API container; API has no published host port. Audio uses a named local volume.
Demucs is not in the base image. Provision/install the optional runtime/weights separately
before claiming separation support. No cloud deployment or external infrastructure was made.

## Operational constraints
No auth/multitenancy, durable job queue, or registry reconstruction at process restart.
Do not expose to the Internet. Project JSON can be restored on browser reload while the
API runs; process restart loses in-memory handles even though files remain on disk.
Stop services before manual backup; copy the workspace and browser JSON together. Do
not delete owner audio as “cleanup.” Failed verified exports are never published.
For rollback, stop the service and use a reviewed prior version without overwriting assets.
Keep original stems immutable. Human acceptance, real-model smoke, security scan and
container startup must be performed before a production-readiness claim.
