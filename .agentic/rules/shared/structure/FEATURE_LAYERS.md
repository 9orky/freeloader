---
doc_class: policy
rule_kind: policy
audience: agent
purpose: Define allowed layers and dependency direction inside a layered module.
applies_when:
  - The module has explicit layers that constrain placement.
  - Dependency direction must be enforced inside the module.
tags:
  - structure
  - layers
  - onion
  - dependencies
read_directly: false
escalation_paths:
  - FEATURE_FILE_TREE.md
  - ../architecture/DEPENDENCIES.md
  - ../architecture/OWNERSHIP.md
---

# Layered Or Onion Module

## Required Decisions

- Name the allowed layers or rings.
- Name the inward dependency direction between those layers or rings.
- Name the owning layer or ring for each touched responsibility.

## Core Rules

- Use only layers or rings that impose meaningful placement and dependency constraints.
- A layered or onion module keeps dependency direction explicit and inward-only.
- Outer layers or rings may depend inward on stable seams; inner layers or rings must not depend outward.
- Each responsibility belongs to one owning layer or ring.
- Concrete layer or ring names may vary by project if their dependency meaning stays explicit.
- Reject cross-layer shortcuts that bypass the chosen seam.
- Local narrowing may choose the concrete layer names, optional subset, and default starter scaffolds for a project.
- Local narrowing must not invert the inward dependency model or weaken seam-based boundaries.

## Review Checks

- The allowed layers or rings are explicit.
- Dependency direction is explicit and inward-only.
- Cross-layer shortcuts are rejected.
- The layered or onion model constrains real decisions.
- Any local narrowing keeps dependency meaning stricter rather than looser.
