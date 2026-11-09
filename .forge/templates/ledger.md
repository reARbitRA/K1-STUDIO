---
id: "TEMPLATE-LEDGER"
title: "Ledger template"
type: "template"
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

# Ledger entry template
Append only the entry below to the live ledger. Do not insert frontmatter mid-file.
Do not refresh old entries or old ledger frontmatter on append.

## Actual ISO8601 UTC · session ID · agent Arena · existing HEAD → actual resulting HEAD
**Did:** Tasks and outcomes, real PR numbers if opened.
**Specs touched:** IDs and authorized transitions, or none.
**Decisions proposed:** Real ADR IDs or none.
**Learned:** Links with provenance.
**Verification:** Exact commands, exit codes, output summary; explicitly list unrun checks.
**Handoff:** Concrete next step and blockers. If uncommitted, say “working tree”.
