# ADR 0001: Blocks Are Validated Terraform Definition Units

## Status

Proposed

## Context

Freeloader's block system exists to let projects compose reusable infrastructure and
deployment units from a catalog of predefined building blocks.

Each block is defined by two coupled concerns:

- a machine-readable contract that describes metadata, configuration, dependencies,
  outputs, and costs
- a Terraform source directory that can be copied into an ephemeral workspace and run

The current refactor in `src/freeloader/block_clean/` is separating these concerns
across domain, application, and infrastructure layers. We want an explicit decision
record for the assumptions that drive this design.

The legacy `src/freeloader/block/` package is migration reference material only. It
helps preserve behavior during the refactor, but it is not the target architecture.

## Decision

### 1. A block is a definition unit made of contract plus Terraform assets

The canonical source of blocks is the repository-local `src/blocks` catalog. This
default may be overridden with `FREELOADER_BLOCKS` when loading an alternative block
catalog for development, tests, or custom deployments.

The selected blocks root is expected to contain provider/block folders with a
`block.yml` contract and a `main.tf` entrypoint.
Templates or auxiliary files remain part of the same source unit.

This means a block is not just a Terraform folder and not just a schema document. It
is the combination of both:

- the contract describes what the block is and what it needs
- the Terraform assets implement how the block is provisioned

### 2. Block contracts are validated with Pydantic at load time

Block definitions are represented as Pydantic models so that malformed contracts fail
when they are loaded, not later during provisioning.

The contract owns:

- metadata such as description, layer, and tech-stack requirements
- configuration field declarations and defaults
- declared provided ports and required ports
- cost metadata

Infrastructure code may normalize source YAML into the canonical schema shape before
validation, but the validated contract object is the source of truth afterwards.

### 3. Manifest defaults and provisioning variables are different stages

Defaults declared in the contract are used to produce user-facing project manifest
configuration. This is a read-model concern.

During manifest generation, blocks that cannot be satisfied at manifest time are
excluded from the generated config surface. In practice this means:

- blocks requiring unavailable auth-backed secrets are excluded
- blocks requiring tech stack data are excluded when the required tech stack fields
  are not available

Provisioning variables are assembled later from multiple sources. The final Terraform
variable set is staged in this order:

- explicit block config supplied from the manifest
- late-bound secrets fetched during provisioning
- dependency outputs resolved from earlier blocks in the same plan
- project-derived defaults such as `project_name_default` and `target_folder`

This keeps secret material and dependency outputs out of the project manifest while
still allowing the manifest to capture stable, reviewable configuration.

### 4. Secret hydration is a provisioning concern, not a manifest concern

Secret-backed configuration fields are declared in the contract schema, but their
values are not materialized in block manifests. They are fetched during provisioning
through a `SecretsReader` abstraction and merged into the Terraform variable set just
before Terraform commands are run.

This decision keeps sensitive values out of persisted manifests and separates config
declaration from secret retrieval.

### 5. Provisioning is performed in dedicated workspaces with early validation

Each block is provisioned from its own ephemeral workspace directory. Before `apply`,
the block's Terraform assets are copied into that workspace and Terraform is executed
through an early validation flow:

- copy assets into a per-block resource folder
- run `terraform init`
- run `terraform plan`
- when dependency inputs are available, refresh init/plan with those values
- only then run `terraform apply`

The goal is to reduce mid-run failure risk by surfacing initialization and planning
problems as early as possible.

### 6. The refactor must keep block aspects distinct

The system distinguishes multiple valid representations of “a block”, each with a
separate responsibility:

- `BlockContract`: validated schema for definition-time rules
- `Block`: pure domain entity identified by `BlockId` and carrying a validated contract
- `SourceBlock`: infrastructure wrapper pairing a domain block with a source folder on disk
- `BlockRef`: manifest/runtime reference to a block chosen by a project
- `ResolvedBlock`: a block reference after dependency resolution, with concrete input bindings
- `ProvisioningResource`: ephemeral workspace where Terraform is executed for one block

We explicitly do not treat these as the same concept, because definition, selection,
resolution, and execution have different invariants and different dependencies.

## Consequences

### Positive

- Block schema errors fail early at load time.
- The manifest can stay declarative and mostly stable.
- Secrets stay out of project manifests.
- The default catalog is predictable in-repo while still allowing alternate catalogs.
- Dependency wiring is explicit and resolved before runtime variable assembly.
- Terraform execution is isolated per block and validated before apply.
- The architecture can keep domain objects free of filesystem and Terraform concerns.

### Trade-offs

- The system has several block representations instead of one convenience object.
- Provisioning still assembles its final Terraform variables as plain dictionaries,
  not as a dedicated domain type.
- Supporting both a default catalog and an override path adds a small amount of
  discovery policy to the infrastructure layer.
- A complete end-to-end guarantee depends on Step 4 integration work, not only on the
  `block_clean` package internals.

## Current Refactor Alignment

The current `block_clean` refactor is aligned with this ADR in the following ways:

- domain contract validation exists in `domain/entity.py`
- source loading and YAML normalization exist in `infrastructure/loader.py`
- manifest defaults and manifest-time filtering are computed in `application/queries.py`
- secret hydration exists in `infrastructure/runner.py`
- dependency-aware provisioning orchestration exists in
  `application/services/provisioner/service.py`
- the definition/runtime/execution representations are explicitly separated across
  `Block`, `SourceBlock`, `BlockRef`, `ResolvedBlock`, and `ProvisioningResource`

## Gaps And Follow-up

The refactor is close to the intended model, but there are still a few boundaries to
finish or tighten:

- the new API is implemented in `block_clean`, but cut-over to `block` is still a Step 4 task
- the final Terraform variable payload is still an implicit merged mapping rather than
  an explicitly named model

## Deferred Follow-up

Create a later ADR focused only on runtime policy, including dependency resolution,
secret policy, and workspace lifecycle, once the package cut-over is complete.