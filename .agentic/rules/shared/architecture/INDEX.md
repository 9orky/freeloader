---
doc_class: navigational
rule_kind: navigation
audience: agent
purpose: Route structural questions about ownership, boundaries, and dependency direction.
applies_when:
  - The task needs placement or boundary guidance before coding or refactoring.
tags:
  - architecture
  - routing
entrypoint: true
read_strategy: progressive
read_directly: false
child_paths:
  - OWNERSHIP.md
  - BOUNDARIES.md
  - DEPENDENCIES.md
---

# Architecture

## Use This Branch When

- The task needs a structural decision before implementation can proceed.
- The current ambiguity is about ownership, public boundary, or dependency direction.

## Stop Or Descend

- Read [OWNERSHIP.md](OWNERSHIP.md) when the main question is which enclosure owns the responsibility.
- Read [BOUNDARIES.md](BOUNDARIES.md) when the main question is what should stay public or private.
- Read [DEPENDENCIES.md](DEPENDENCIES.md) when the main question is which direction a dependency may flow.
- Stop here if the task already has a clear owner, boundary, and dependency direction.

## Review Checks

- Only one structural question drives the next read.
- The shallowest matching leaf is chosen.
