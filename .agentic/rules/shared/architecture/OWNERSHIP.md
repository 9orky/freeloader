---
doc_class: policy
rule_kind: policy
audience: agent
purpose: Decide the owning enclosure for a responsibility before implementation or refactoring.
applies_when:
  - The task touches code that could belong to more than one feature, module, or layer.
tags:
  - architecture
  - ownership
read_directly: false
escalation_paths:
  - BOUNDARIES.md
  - DEPENDENCIES.md
---

# Ownership

## Required Decisions

- Name the owning enclosure.
- Name the owning module when the enclosure contains more than one module.
- Name the owning layer when the module is layered.

## Core Rules

- One responsibility has one owner at the current decision level.
- Choose the smallest enclosure that can own the behavior without leaking policy outward.
- Do not split ownership unless an explicit seam justifies the split.
- Do not keep legacy placement just because the current file already exists there.

## Review Checks

- The owner is explicit.
- Ownership is not shared by default.
- The chosen owner matches the intended boundary.
- The choice does not widen public API just to avoid wiring.
