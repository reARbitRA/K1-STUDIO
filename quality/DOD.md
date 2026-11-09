---
id: "FORGE-DOD"
title: "Definition of done"
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

# Definition of Done

A product task is DONE only when all apply:
- [ ] An explicitly human-approved spec and plan authorize its scope.
- [ ] Every in-scope AC maps to an executed passing `test_ac_<n>_<slug>` test.
- [ ] Full product suite and methodology checks pass; no new silent skip/xfail.
- [ ] Lint, typecheck, and secret scanning pass.
- [ ] Exact paths and actual evidence are updated in TRACE; spec metadata advances lawfully.
- [ ] ENV/runbooks/knowledge are updated when interfaces or operations change.
- [ ] STATE and append-only LEDGER record actual results and blockers.
- [ ] A PR contains verification output and awaits independent review.

Methodology-only tasks substitute tooling tests for product ACs and explicitly say
“no product spec.” They still require checks, evidence, handoff, and a PR before DONE.
A task awaiting a PR, checks, or reviewer is REVIEW, not DONE. Only a human can mark a
spec VERIFIED after exercising the deployed acceptance criteria. No product deployment
or product test/coverage claim can be made from successful scaffold checks.
