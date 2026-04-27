---
doc_class: navigational
rule_kind: navigation
audience: agent
purpose: Route code-change work that reshapes existing implementation.
applies_when:
  - The task changes existing code structure rather than adding a new slice only.
tags:
  - change
  - routing
entrypoint: true
read_strategy: progressive
read_directly: false
child_paths:
  - REFACTORING.md
---

# Change

## Use This Branch When

- The task restructures existing implementation.
- The task may need a fresh slice instead of in-place repair.

## Stop Or Descend

- Read [REFACTORING.md](REFACTORING.md) when target-design refactoring guidance is needed.
- Stop here if the task is only new implementation without legacy reshaping.

## Review Checks

- The branch is used only for structural change work.
- New-slice work is not mislabeled as refactoring.
