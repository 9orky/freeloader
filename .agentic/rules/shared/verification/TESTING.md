---
doc_class: policy
rule_kind: policy
audience: agent
purpose: Govern seam selection, test scope, and assertion quality.
applies_when:
  - The task needs tests or another proof of behavior.
tags:
  - verification
  - testing
read_directly: false
escalation_paths:
  - ../architecture/BOUNDARIES.md
  - ../architecture/DEPENDENCIES.md
---

# Testing

## Required Decisions

- Name the seam under test.
- Choose the smallest scope that proves the behavior.
- State what behavior the assertions must prove.

## Core Rules

- Prefer the highest valid seam that gives clear behavioral signal.
- Test modules directly only when the module owns the relevant seam.
- Do not add test-only production seams, flags, or exports.
- Assert behavior and contract shape, not private implementation detail.

## Review Checks

- The public seam under test is explicit.
- The smallest proving scope is chosen.
- No test-only production seam is added.
- Assertions prove behavior rather than internals.
