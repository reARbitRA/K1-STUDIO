---
id: "FORGE-SECURITY"
title: "Security baseline"
type: "quality"
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

# Security baseline

1. Never commit credentials, private keys, user audio, or credential-bearing logs.
   Gitignore reduces accidents; it is not a security boundary. Scan history and worktree.
2. Use Arena-managed authentication. Do not generate deploy keys, change remotes, or
   collect credentials unless separately authorized. See `ops/KEYS.md`.
3. Least privilege: read-only CI permissions; no pull_request_target execution of untrusted
   code with secrets. PR jobs use checkout without persisted credentials.
4. Do not log sensitive inputs; product privacy, upload limits, path validation, dependency
   policy, and local-network exposure need approved specs before a server is added.
5. Gitleaks 8.24.2 is downloaded from the official release in CI and checked against that
   release's SHA-256 manifest. No broad allowlists; review each suppression individually.
6. On suspected exposure: stop, notify the owner, revoke/rotate externally, then clean
   history with a separately approved plan. Deleting a file does not revoke a credential.
7. Maintainers must protect main: require PR, human review, checks test/lint/typecheck/
   secret-scan/forge-lint, no force pushes/deletion, and no agent bypass. Prefer linear
   history and squash/rebase merges if enabled. These settings are not changed here.
   Write credentials can still exfiltrate repository data, modify unprotected refs, or
   trigger workflows; branch protection does not make a leaked key harmless.
