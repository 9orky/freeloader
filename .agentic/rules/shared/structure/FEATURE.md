---
doc_class: policy
rule_kind: policy
audience: agent
purpose: Define stricter ownership and boundary expectations for a feature module.
applies_when:
  - The module owns one user-visible or business capability.
  - Feature boundaries matter to placement, API shape, or dependency control.
tags:
  - structure
  - feature
  - boundary
read_directly: false
escalation_paths:
  - FEATURE_LAYERS.md
  - ../architecture/OWNERSHIP.md
  - ../architecture/BOUNDARIES.md
---

# Feature Module

## Required Decisions

- Name the capability the feature owns.
- Name the public seam other modules may use.
- Name any cross-feature collaboration that must remain narrow.

## Core Rules

- A feature is a module with stricter ownership and boundary expectations.
- The feature owns one coherent capability, not a grab bag of adjacent concerns.
- Cross-feature access goes through the smallest stable seam.
- The feature still exposes only a minimal API.

## Review Checks

- Capability ownership is explicit.
- The feature boundary is visible.
- Cross-feature access is narrow.
- Feature rules do not widen the public surface.
