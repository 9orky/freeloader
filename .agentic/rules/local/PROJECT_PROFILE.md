---
doc_class: rule
rule_kind: project_profile
audience: agent
purpose: Capture Freeloader's stable product and domain model.
applies_when:
  - Understanding feature ownership.
  - Deciding where new concepts belong.
tags:
  - freeloader
  - product
  - ownership
---

# Freeloader Project Profile

Freeloader is a Python CLI that composes deployment infrastructure for indie projects from Terraform-backed blocks.

The core idea is excellent and worth preserving: the project turns repetitive free-tier deployment choreography into a typed, inspectable composition problem. Blocks describe infrastructure contracts, providers describe local/provider capability, secrets keep credentials contained, and project orchestration assembles the manifest. That separation is the genius of it.

## Stable Feature Responsibilities

- `project`: composition, manifest generation, planning diagnostics, project lifecycle commands.
- `block`: block definitions, contracts, defaults, Terraform asset loading, provisioning and destroy execution.
- `service_providers`: provider identity, authorization, billing, and local support/capability reporting.
- `secrets`: secret persistence, retrieval, and availability checks without leaking values.
- `shared.tech`: normalized detected language, framework, and package-manager facts.
- `shared.terraform`, `shared.console`, `shared.registry`, `shared.io`: cross-feature utilities only.

## Placement Rules

- Put selection policy in `project`, not in `block`, `service_providers`, `secrets`, or `shared`.
- Put requirement facts in `block`; do not make blocks inspect provider support.
- Put provider capability facts in `service_providers`; do not make providers understand block contracts.
- Put secret availability in `secrets`; planning should consume keys and availability, never raw values.
- Put normalized project stack facts in `shared.tech`; do not turn it into a policy engine.

## Product Bias

Favor explainable, inspectable deployment composition over magic. When a block is omitted, the system should eventually be able to say why.
