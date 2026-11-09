---
id: "TEMPLATE-SPEC"
title: "Spec template"
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

# SPEC-NNN — Title

Copy this template, replace TEMPLATE ID with SPEC-NNN, type with spec, status with
DRAFT, owner/dates/tags with real values. Request human review; never self-approve.

## 1. Summary (at most three sentences)
## 2. Motivation
Link to approved vision / source brainstorm.
## 3. User stories
- US-1:
## 4. Scope
### In scope
### Out of scope
## 5. Behavioral contract
### 5.1 Interfaces
Exact inputs, outputs, versions, limits.
### 5.2 Rules
- R1:
### 5.3 Data
Schema, migration/reversal, invariants, retention.
### 5.4 Errors
Codes, response bodies, retry behavior.
## 6. Acceptance criteria
- AC-1: Given … when … then …
## 7. Non-functional requirements
Measurable latency/resource/correctness bounds and workload.
## 8. Security considerations
Threats, mitigations, privacy.
## 9. Open questions
- OQ-1: Resolve via a human decision before implementation.
## 10. Verification plan
Real executable command; AC-1 → test_ac_1_<slug> in an explicit test path.
## 11. Trace
Plan / tasks / ADRs / exact TRACE paths; add actual IDs when allocated.
