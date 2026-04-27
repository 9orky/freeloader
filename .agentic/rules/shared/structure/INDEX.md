---
doc_class: navigational
rule_kind: navigation
audience: agent
purpose: Classify the target folder at the shallowest structural level that fits.
applies_when:
  - The task needs structural rules for a code folder or package.
  - The agent must decide whether deeper specialization is required.
tags:
  - structure
  - routing
  - module
entrypoint: true
read_strategy: progressive
read_directly: false
child_paths:
  - MODULE.md
  - FEATURE.md
  - FEATURE_LAYERS.md
  - FEATURE_FILE_TREE.md
---

# Structure

## Use This Branch When

- The task needs to classify a folder before applying ownership, execution, or verification rules.
- The target may be a plain module, a feature module, or a layered specialization.

## Stop Or Descend

- Read [MODULE.md](MODULE.md) first for the base module rule.
- Read [FEATURE.md](FEATURE.md) when the module is also a feature-shaped unit.
- Read [FEATURE_LAYERS.md](FEATURE_LAYERS.md) only when explicit layers are part of the contract.
- Read [FEATURE_FILE_TREE.md](FEATURE_FILE_TREE.md) only when the layer model implies deterministic tree growth.
- Stop here if the task does not need structural classification.

## Review Checks

- Module classification happens before deeper specialization.
- Feature and layer rules are opened only when the stricter specialization is real.
- The agent stops at the shallowest structural rule that fits.
