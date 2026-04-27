---
doc_class: policy
rule_kind: policy
audience: agent
purpose: Define deterministic file-tree growth for a layered module.
applies_when:
  - The layered module has a required or strongly preferred file-tree pattern.
  - New files should be placed according to layer-owned growth rules.
tags:
  - structure
  - file-tree
  - layers
  - onion
read_directly: false
escalation_paths:
  - FEATURE_LAYERS.md
  - ../architecture/BOUNDARIES.md
  - ../change/REFACTORING.md
---

# Layered Or Onion File Tree

## Required Decisions

- Name the required top-level folders or files for the module.
- Name the owning layer or ring for each new file.
- Name the stable public seams the tree must preserve.

## Core Rules

- The file tree grows from the chosen layered or onion model rather than from convenience.
- Add a file in the owning layer or ring first, not in the nearest existing folder.
- Keep public seams stable while internal structure grows inward.
- Do not invent new tree branches unless the current layer or ring rules require them.
- Local narrowing may define concrete layer names, root seam file names, and default starter scaffolds.
- Local narrowing must not add convenience branches that bypass ownership or weaken inward dependency boundaries.

## Review Checks

- Tree growth follows layer or ring ownership.
- Public seams remain minimal.
- New files are not placed by convenience alone.
- The tree reflects responsibility and dependency rules.
- Any local narrowing changes names or scaffolds without weakening the ownership model.
