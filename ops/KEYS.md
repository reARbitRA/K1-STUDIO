---
id: "FORGE-KEYS"
title: "Credential policy and inventory"
type: "ops"
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

# Credential policy and inventory

Use the existing Arena-managed GitHub connection; no deploy key was generated and no
remote/authentication settings were changed. Authentication errors require reconnecting
GitHub in Arena, never asking for secrets in chat.

| Credential | Public fingerprint | Created | Policy expiry | Purpose | Status |
| --- | --- | --- | --- | --- | --- |
| Arena-managed GitHub authentication | Not exposed to repo | Managed externally | Managed externally | Authorized repository operations | Provided by platform; not independently audited |

## Optional deploy keys — only on explicit owner authorization
Generate a dedicated ed25519 key outside the repository, never print private material,
share only the public key, and record fingerprint/creation/owner/expiry metadata here.
A human grants scope and installs the public key; no automation changes access policy.
One key per workspace/repo, rotate at most every 30 days and immediately on suspicion.
Prefer short-lived GitHub App tokens when available. Do not repoint origin or create
keys as a side effect of bootstrap. Branch protection limits merges, not every capability
of a leaked write credential. Revoke externally before attempting repository cleanup.
