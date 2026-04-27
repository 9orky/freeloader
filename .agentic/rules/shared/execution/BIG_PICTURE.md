---
doc_class: execution
rule_kind: execution
audience: agent
purpose: Define phase-level execution before step files exist.
applies_when:
  - The first execution artifact for the work is being written.
  - Approved phases do not exist yet.
tags:
  - execution
  - big-picture
stage: big_picture
same_artifact_family: execution
read_directly: false
escalation_paths: []
---

# Big Picture

## Required Sections

- `File Tree`
- `Goal`
- `Phases`
- `Acceptance`
- `Open Questions`

## Optional Sections

- `Execution Frame`
- `Strategic Model`

## File Tree Rules

- `File Tree` is the first section.
- The big-picture artifact is named `PLAN.md`.
- The tree lists folders and files only.
- Class, method, and function signatures are not allowed.
- If `Phases` names layers or rings, `File Tree` and `Phases` use the same set.

## Phase Rules

- `Phases` is the center of the document.
- Each phase states objective, owning layer or ring, inputs, outputs, and acceptance.
- Phase order becomes step order after approval.

## Strategic Model Gate

- Add `Strategic Model` only when business language, bounded context, or domain structure changes materially.
- If domain structure is unchanged, do not add the section.

## Review Checks

- The file tree comes first.
- The artifact filename is `PLAN.md`.
- The document stays at file-tree, phase, and contract level.
- Phases translate directly into step files.
- Overall acceptance is explicit.
- Open questions capture remaining risks or unknowns.

## Handoff Checks

- Step files are not created before big-picture approval.
- Approved phases can be expanded without reordering.
- Implementation detail stays out of the big-picture artifact.