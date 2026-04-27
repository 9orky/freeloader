---
doc_class: rule
rule_kind: architecture
audience: agent
purpose: State local architecture constraints that agents must preserve.
applies_when:
  - Adding modules or moving code.
  - Changing imports or public package exports.
  - Adding feature APIs or cross-feature calls.
tags:
  - boundaries
  - layers
  - imports
---

# Freeloader Architecture Rules

## Feature Surface

- Feature package roots are the only cross-feature import surface.
- Legal cross-feature examples: `from freeloader.block import Blocks`, `from freeloader.service_providers import ServiceProviders`.
- Illegal cross-feature examples: `freeloader.block.application.queries`, `freeloader.service_providers.infrastructure.providers`.
- A feature root exports at most a CLI app and/or one machine-facing facade.

## Layer Direction

Allowed direction:

```text
ui -> application -> infrastructure -> domain
application -> domain
infrastructure -> domain
domain -> shared or stdlib
```

Layer-specific rules:

- `domain/` imports only stdlib, same-feature domain modules, and stable `freeloader.shared` facts.
- `infrastructure/` implements contracts and talks to external systems.
- `application/` owns use cases, facades, and orchestration.
- `ui/` wires Typer and presentation only.
- `shared/` never imports a feature.

## Public Seams

- Use `application/interface.py` for machine-facing facades.
- Use `application/__init__.py` as the feature-local UI import surface.
- Use `infrastructure/__init__.py` for factory functions like `load_*`.
- Keep implementation modules private to their feature unless surfaced through the package root.

## Block Asset Contract

- Treat each `src/blocks/<provider>/<block>/block.yml`, `main.tf`, and template set as one coupled unit.
- If a block contract changes, update docs and tests that describe required/provided ports.
- Keep Terraform execution refactors separate from manifest planning refactors unless the task explicitly joins them.
