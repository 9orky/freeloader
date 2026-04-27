---
doc_class: policy
rule_kind: policy
audience: agent
purpose: Define the base rule for any module-shaped folder of program files.
applies_when:
  - The target folder contains program files that should be treated as one owned unit.
  - No stricter feature or layer contract has been established yet.
tags:
  - structure
  - module
  - api
read_directly: false
escalation_paths:
  - FEATURE.md
  - ../architecture/OWNERSHIP.md
  - ../architecture/BOUNDARIES.md
---

# Module

## Required Decisions

- Name the module-owned responsibility.
- Name the minimal public API.
- Distinguish public entrypoints from private internals.

## Core Rules

- A folder of program files forms a module when it owns one coherent responsibility.
- A module exposes only the smallest public API needed by real consumers.
- Do not export helpers, internals, or convenience surfaces without a concrete consumer need.
- Do not assume features or layers unless the structure requires stricter specialization.

## Review Checks

- The folder is treated as one owned unit.
- The public API is smaller than the internal surface.
- Extra exports are rejected.
- Deeper specialization is applied only when justified.
