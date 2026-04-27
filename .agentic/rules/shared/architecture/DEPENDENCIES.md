---
doc_class: policy
rule_kind: policy
audience: agent
purpose: Decide allowed dependency direction for the current structure.
applies_when:
  - The task adds or changes a dependency between folders, modules, or layers.
tags:
  - architecture
  - dependencies
read_directly: false
escalation_paths:
  - OWNERSHIP.md
  - BOUNDARIES.md
---

# Dependencies

## Required Decisions

- Name the source of the dependency.
- Name the target of the dependency.
- State why the direction is valid.

## Core Rules

- Dependency direction must be explicit when structure matters.
- A parent may depend on a child seam only.
- A child must not depend on its consumer.
- Circular dependencies are forbidden.

## Review Checks

- Source and target are explicit.
- Direction matches the chosen structure.
- No circular dependency is introduced.
- The dependency reaches a seam, not private internals.
