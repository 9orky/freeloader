---
doc_class: navigational
rule_kind: navigation
audience: agent
purpose: Route execution work between phase-level and implementation-level execution artifacts.
applies_when:
  - The task needs execution guidance before or during coding.
tags:
  - execution
  - routing
entrypoint: true
read_strategy: progressive
read_directly: false
child_paths:
  - BIG_PICTURE.md
  - STEP.md
---

# Execution

## Use This Branch When

- The task needs an execution artifact before or during implementation.
- The current work should be shaped as a big picture or a single executable step.

## Stop Or Descend

- Read [BIG_PICTURE.md](BIG_PICTURE.md) when phases are not approved yet.
- Read [STEP.md](STEP.md) only after the current phase is approved for execution.
- Stop here if the task does not require an execution artifact.

## Review Checks

- The chosen artifact matches the current execution stage.
- Step execution is not opened before phase approval.