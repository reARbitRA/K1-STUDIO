---
id: FORGE-ENV
title: Environment inventory
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

# Environment inventory

No secret values belong here or in committed `.env` files.

| Name | Purpose | Where set | Default / sensitivity |
| --- | --- | --- | --- |
| PYTHON | make bootstrap interpreter | local make variable | python3; public |
| BASE | actual PR base SHA for ledger diff | local make / CI | omitted locally; public |
| PYTHONPATH | locate Python package under src | dev command/container | src; public |
| K1_WORKSPACE | generated original/canonical/export file directory | backend environment | .workspace; local/private audio, ignored |
| K1_DEMUCS_MODELS | pre-provisioned local Demucs model repository | backend environment | unset → 503; weights never committed/downloaded implicitly |
| K1_ALLOWED_HOSTS | additional explicit comma-separated local backend hostnames | backend environment | localhost/127.0.0.1/testserver plus Arena preview host pattern; not authentication |
| CI | disables browser-test reuse of existing servers | GitHub Actions | automatic; public |
| LD_LIBRARY_PATH | bundled native libraries for test-only Chromium | Playwright launch env | generated ignored .verification/browser-libs/lib; not production |
| GITHUB_TOKEN | GitHub ephemeral checkout token | automatic CI | never print/copy; read-only |

Backend CLI defaults to loopback; use --host 0.0.0.0 only in controlled container/Arena
preview environments. Vite uses relative /api and /ws proxies. No frontend secret or
browser-facing localhost backend URL is used. Browser localStorage stores project JSON,
not raw audio/buffers or credentials. Disk workspace lifetime is owner-managed.
