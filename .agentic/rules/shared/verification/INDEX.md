---
doc_class: navigational
rule_kind: navigation
audience: agent
purpose: Route proof and testing questions.
applies_when:
  - The task needs to prove behavior or choose a testing seam.
tags:
  - verification
  - routing
entrypoint: true
read_strategy: progressive
read_directly: false
child_paths:
  - TESTING.md
---

# Verification

## Use This Branch When

- The task needs to choose what to test and through which seam.
- The task needs proof that a change is complete.

## Stop Or Descend

- Read [TESTING.md](TESTING.md) when the task needs test scope or assertion guidance.
- Stop here if verification strategy is already clear.

## Review Checks

- The verification question is explicit.
- The branch does not duplicate execution guidance.
