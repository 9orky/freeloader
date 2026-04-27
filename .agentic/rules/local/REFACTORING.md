---
doc_class: rule
rule_kind: change_management
audience: agent
purpose: Guide safe refactors in Freeloader.
applies_when:
  - Performing architecture cleanup.
  - Migrating manifest planning or block/provider contracts.
  - Splitting or consolidating services.
tags:
  - refactoring
  - migration
  - validation
---

# Freeloader Refactoring Rules

## Migration Style

- Prefer additive APIs first, migrate callers second, remove transitional paths last.
- Preserve manifest file format until a plan explicitly changes it.
- Keep current CLI behavior stable while adding diagnostics or planning models.
- Avoid broad renames before the new seam has tests.
- Do not mix provisioning DAG redesign into manifest-selection work.

## Refactor Priority

1. Name and test the `project` planning seam.
2. Make `block` expose explicit candidate and requirement metadata.
3. Make `service_providers` return structured support details while keeping boolean helpers.
4. Make `secrets` expose availability checks that do not reveal values.
5. Add CLI diagnostics after the planning report is stable.
6. Remove duplicated filtering and raw id parsing.

## Validation

- Run focused tests for touched features.
- Run `uv run pytest tests/test_architecture.py` when imports, package roots, or layers change.
- Run broader `uv run pytest` before declaring a cross-feature refactor complete.
- Add regression tests for preserved behavior before removing transitional code.
