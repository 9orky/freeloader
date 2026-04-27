---
doc_class: policy
rule_kind: policy
audience: agent
purpose: Decide the public seam and protect private internals.
applies_when:
  - The task may change what is exposed or how callers reach the code.
tags:
  - architecture
  - boundaries
read_directly: false
escalation_paths:
  - OWNERSHIP.md
  - DEPENDENCIES.md
---

# Boundaries

## Required Decisions

- Name the public boundary.
- Name the public seam.
- Name any internal area that must stay private.

## Core Rules

- Expose the minimum public API needed by real callers.
- Keep helpers, policies, and intermediate models private by default.
- Do not widen the API to avoid local composition work.
- Do not deep-import internals across the boundary.

## Review Checks

- The public seam is explicit.
- Private internals remain private.
- No deep import is required.
- The boundary is not widened without a real consumer need.
