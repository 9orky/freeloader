---
doc_class: navigational
rule_kind: navigation
audience: agent
purpose: Route agents into Freeloader-specific rules before changing code.
applies_when:
  - Starting work in this repository.
  - Planning a refactor or architecture change.
  - Touching feature boundaries, block contracts, provider support, secrets, or manifest planning.
tags:
  - freeloader
  - architecture
  - local
entrypoint: true
read_strategy: progressive
read_directly: true
child_paths:
  - PROJECT_PROFILE.md
  - ARCHITECTURE.md
  - REFACTORING.md
---

# Local Freeloader Rules

## Read Order

1. Read [PROJECT_PROFILE.md](PROJECT_PROFILE.md) for the product and ownership model.
2. Read [ARCHITECTURE.md](ARCHITECTURE.md) before changing imports, package exports, feature APIs, or layer placement.
3. Read [REFACTORING.md](REFACTORING.md) before starting any multi-step cleanup or architectural migration.

## Hard Anchors

- Architecture source of truth: [docs/FEATURE_ARCHITECTURE.md](../../../docs/FEATURE_ARCHITECTURE.md)
- Executable boundary checks: `tests/architecture_rules/`
- Agentic config: [.agentic/agentic.yaml](../../agentic.yaml)

## Review Checks

- The change keeps cross-feature imports at package roots.
- The change preserves layer direction.
- The change strengthens the project planning seam instead of creating direct `block <-> service_providers` coupling.
- Validation includes targeted tests and `uv run pytest tests/test_architecture.py` when boundaries move.
