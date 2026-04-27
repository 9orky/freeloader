---
doc_class: execution
rule_kind: execution
audience: agent
purpose: Define one approved phase as an implementation-level execution artifact.
applies_when:
  - A big-picture phase has been approved.
  - The next execution artifact needs implementation detail.
tags:
  - execution
  - step
stage: step
same_artifact_family: execution
read_directly: false
escalation_paths: []
---

# Step

## Required Sections

- `Implementation Tree`
- `Goal`
- `Step Contract`
- `Execution`
- `Verification`
- `Completion`

## Implementation Tree Rules

- `Implementation Tree` is the first section.
- The step artifact is named `PLAN_STEP_0X.md`.
- The `0X` suffix matches the approved phase order from `PLAN.md`.
- The tree reuses the approved big-picture tree and adds implementation signatures.
- Planned classes, functions, and seams are named where they will be implemented.

## Step Contract Rules

- State inputs, outputs, scope, out-of-scope, owning layer, and dependency direction.
- Keep the step narrow enough to finish and verify as one unit.

## Execution Rules

- Use ordered work items.
- Allow local adaptation only if the goal and boundary stay intact.
- Stop and escalate when ownership, boundary, or dependency assumptions break.

## Review Checks

- The implementation tree comes first.
- The artifact filename matches `PLAN_STEP_0X.md`.
- Signatures are present where implementation is planned.
- Scope is narrow and verifiable.
- Verification matches the step goal.
- Completion state is explicit.

## Handoff Checks

- The step still matches an approved big-picture phase.
- Completion leaves the next step with a clear starting state.
- Any drift from the big picture is recorded before proceeding.