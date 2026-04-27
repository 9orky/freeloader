---
doc_class: navigational
rule_kind: navigation
audience: agent
purpose: Route canonical shared rules to the shallowest category branch that fits the task.
applies_when:
  - The task needs reusable packaged guidance.
tags:
  - shared
  - routing
  - rules
entrypoint: true
read_strategy: progressive
read_directly: true
child_paths:
  - structure/INDEX.md
  - architecture/INDEX.md
  - change/INDEX.md
  - execution/INDEX.md
  - verification/INDEX.md
---

# Shared Rules

## Use This Branch When

- The next read should come from canonical reusable guidance.

## Stop Or Descend

- Stop here if the task does not need branch-specific rules yet.
- Descend only to the first shared branch whose assumptions fit the current task.
- Prefer the shallowest matching branch over deeper specialization.
- For code-shape questions, classify structure before applying architecture, change, or verification rules.
- If repository-specific narrowing is still needed after the shared branch is known, switch to the generated local profile in the project contract rather than expecting another packaged shared branch.

## Branches

- [structure/INDEX.md](structure/INDEX.md): classify a target as a module, feature module, or layered specialization
- [architecture/INDEX.md](architecture/INDEX.md): ownership, boundary, and dependency rules for structural placement
- [change/INDEX.md](change/INDEX.md): rules for reshaping or replacing existing implementation
- [execution/INDEX.md](execution/INDEX.md): execution artifacts used before and during implementation
- [verification/INDEX.md](verification/INDEX.md): testing and proof rules for validating behavior

## Review Checks

- The next shared read is explicit.
- No deeper shared branch is opened without a matching need.
- Structure is classified before deeper structural constraints are applied.
- Shared guidance remains the reusable baseline before any local project profile is consulted.