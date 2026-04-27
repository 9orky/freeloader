---
doc_class: policy
rule_kind: policy
audience: agent
purpose: Govern target-design refactoring and fresh-slice decisions.
applies_when:
  - Existing code must be reshaped toward a clearer target design.
tags:
  - change
  - refactoring
read_directly: false
escalation_paths:
  - ../architecture/OWNERSHIP.md
  - ../architecture/BOUNDARIES.md
  - ../verification/TESTING.md
---

# Refactoring

## Required Decisions

- State the target design first.
- Decide between in-place refactor and fresh slice.
- State the verification seam that proves the new path works.

## Core Rules

- Start from the target design, not the legacy layout.
- Treat legacy structure as weak behavioral reference only.
- Use a fresh slice when ownership, boundary, or structure changes materially.
- Keep both paths active only long enough to verify the replacement.
- Remove migration scaffolding after the verified swap.

## Review Checks

- The target design is explicit.
- The fresh-slice decision is explicit.
- Legacy structure is not treated as architectural authority.
- A verified swap exists before cleanup.
