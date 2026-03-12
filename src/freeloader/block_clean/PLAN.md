# Block Feature — Clean Architecture Refactor Plan

Reference document for migrating `src/freeloader/block/` to the layered feature
architecture defined in `docs/FEATURE_ARCHITECTURE.md`. The new package will be
developed in `src/freeloader/block_clean/` and then replace `block/` when complete.

---

## 1. What Is Wrong With the Current Structure

| Problem | Location |
|---|---|
| `ports/` directory exists | Architecture says "no `ports/` directory" |
| `base.py` at root holds `BlockId` (value object) and `SecretsReader` (abstract interface) | Should be in `domain/` |
| `contract.py`, `layer.py`, `context.py`, `error.py` live at the package root | Domain concepts scattered at the wrong level |
| `facade.py` at root wraps everything but has no clear layer identity | Should become `application/interface.py` as `Blocks` class |
| `orchestrator.py` at root is a query use-case disguised as a helper | Should become `application/queries.py` |
| `provisioner.py` at root is a command use-case | Should become `application/commands.py` |
| `runner.py` at root does Terraform I/O | Should be `infrastructure/runner.py` |
| `provision/models.py` imports `Block` from `infrastructure/` | Domain models must not depend on infrastructure |
| `provision/resource.py` is I/O but lives in a shared `provision/` sub-package | Should be `infrastructure/resource.py` |
| `infrastructure/block.py` couples filesystem paths with domain identity/contract | Domain `Block` entity should be path-free; paths belong in infrastructure |
| `resolver/` is pure logic with no I/O but lives outside any layer | Pure logic belongs in `domain/` |
| No `ui/` layer defined | Fine — block has no CLI — but should be explicit |

---

## 2. Target Directory Layout

```
src/freeloader/block_clean/
│
├── __init__.py                  # Re-exports: Blocks facade, BlockRef
│
├── domain/
│   ├── __init__.py              # Layer enum + LAYER_ORDER constant
│   ├── value_object.py          # BlockId
│   ├── entity.py                # Block, BlockRef, ResolvedBlock,
│   │                            #   OutputReference + contract schema
│   ├── repository.py            # SecretsReader (ABC), BlockRepository (ABC)
│   ├── errors.py                # BlockError, DAGError + subclasses
│   └── resolver.py              # DAGResolver, ProvidesMapper, TopologicalSorter
│
├── application/
│   ├── __init__.py              # Re-exports: Blocks, report types
│   ├── interface.py             # Blocks façade — used by other features
│   ├── commands.py              # provision_blocks(), destroy_blocks()
│   ├── queries.py               # get_manifest_configs()
│   └── services/
│       ├── __init__.py          # Re-exports public services
│       └── provisioner/
│           ├── __init__.py      # Re-exports service + report types
│           ├── models.py        # ProvisioningPlan/Report dataclasses
│           └── service.py       # BlockProvisioningService orchestration
│
└── infrastructure/
   ├── __init__.py              # load_block_repository(), load_secrets_reader()
   ├── block.py                 # SourceBlock — domain Block + source Path (infra-only)
   ├── loader.py                # FileSystemBlockLoader(BlockRepository)
   ├── runner.py                # BlockRunner, VariablesBuilder — Terraform I/O
   ├── resource.py              # ProvisioningResource — temp dir management
   └── secrets.py               # SecretsAdapter — adapts Secrets facade to SecretsReader
```

No `ui/` layer. The `block` feature exposes a machine API (`Blocks`) consumed by the
`project` feature. There are no user-facing Typer commands.

---

## 3. Concept-to-File Mapping

### domain/

| Current location | New location | Notes |
|---|---|---|
| `layer.py::Layer`, `LAYER_ORDER` | `domain/__init__.py` | Domain-scoped constants |
| `base.py::BlockId` | `domain/value_object.py` | Typed str wrapper |
| `contract.py` (all classes) | `domain/entity.py` | `BlockContract`, `BlockMeta`, `ConfigField`, `PortSpec`, `CostTier`, `FreeTierLimit`, `BlockCostSpec` are pure domain schema — no path, no I/O |
| `context.py::OutputReference` | `domain/entity.py` | Pure domain dependency reference |
| `resolver/base.py::BlockRef`, `ResolvedBlock` | `domain/entity.py` | Core domain reference types; `BlockRef` keeps its Pydantic base for manifest parsing |
| `base.py::SecretsReader` | `domain/repository.py` | Renamed: abstract `SecretsReader` |
| _(new)_ `BlockRepository` | `domain/repository.py` | Abstract interface with `load_all()`, `load_by_ids()`, `dump_assets()` |
| `error.py::BlockError` | `domain/errors.py` | Consolidated with resolver errors |
| `resolver/error.py` | `domain/errors.py` | `DAGError`, `MissingRequirement`, `AmbiguousProvider`, `CircularDependency`, `DuplicateBlockId` |
| `resolver/dag.py::DAGResolver` | `domain/resolver.py` | Pure graph logic, no I/O |
| `resolver/mapper.py::ProvidesMapper` | `domain/resolver.py` | Pure logic |
| `resolver/sorter.py::TopologicalSorter` | `domain/resolver.py` | Pure logic |

**New domain `Block` entity** — created fresh in `domain/entity.py`:
```python
@dataclass(frozen=True)
class Block:
    id: BlockId
    contract: BlockContract
```
This replaces neither the current `infrastructure/block.py::Block` (which is I/O-aware)
nor the current absent domain entity. It is the pure domain representation of a block
definition, without any filesystem coupling.

### application/

| Current location | New location | Notes |
|---|---|---|
| `ports/interface.py::_SecretsAdapter` | `infrastructure/secrets.py` | Moved to infra (it talks to the `Secrets` feature) |
| `ports/interface.py` free functions (`get_manifest_configs`, `provision_project`, `destroy_project`) | Absorbed into `application/interface.py::Blocks` | These become methods on the façade |
| `facade.py::BlocksFacade` | `application/interface.py::Blocks` | Renamed and restructured; all wiring stays here |
| `orchestrator.py::ConfigOrchestrator.build_manifest_configs` | `application/queries.py::get_manifest_configs()` | Extracted to query function |
| `provisioner.py::Provisioner.provision` | `application/commands.py::provision_blocks()` + `application/services/provisioner/service.py` | Command wires the service; orchestration lives in the service |
| `provisioner.py::Provisioner.destroy` | `application/commands.py::destroy_blocks()` + `application/services/provisioner/service.py` | Same split as provision |
| `provisioner.py::Provisioner.plan` | `application/services/provisioner/service.py::build_plan()` | Planning stays with orchestration |
| `provision/models.py` | `application/services/provisioner/models.py` | `ProvisioningPlan`, `ProvisioningStep`, `ProvisioningReport`, `AppliedStepReport`, `DestroyReport`, `DestroyStepReport` move into the service package; `ProvisioningStep.block` changes type from infra `Block` to domain `Block` |

**`Blocks` façade** (`application/interface.py`):
```python
class Blocks:
    @classmethod
    def for_project(cls, project_root: Path) -> "Blocks": ...

    def provision(self, resources_root: Path, block_refs: list[BlockRef]) -> ProvisioningReport: ...
    def destroy(self, resources_root: Path, block_refs: list[BlockRef]) -> DestroyReport: ...
    def manifest_configs(self, tech_stack, full_config, project_name) -> dict: ...
```

The facade stores only feature-scoping primitives (`project_root` here). Secrets are
loaded by application use-cases through infrastructure factory functions so public
command/query signatures stay aligned with `docs/FEATURE_ARCHITECTURE.md`.

### infrastructure/

| Current location | New location | Notes |
|---|---|---|
| `infrastructure/block.py::Block` | `infrastructure/block.py::SourceBlock` | Renamed to signal infra status; holds `block: Block` (domain) + `source_folder: Path`; retains `dump_assets()` |
| `infrastructure/loader.py::BlockLoader` | `infrastructure/loader.py::FileSystemBlockLoader(BlockRepository)` | Implements the domain `BlockRepository` ABC; `load_all()` / `load_by_ids()` return domain `Block`; `dump_assets()` copies files using stored path |
| `runner.py::BlockRunner` | `infrastructure/runner.py::BlockRunner` | No change in logic; now clearly scoped to infra |
| `runner.py::VariablesBuilder` | `infrastructure/runner.py::VariablesBuilder` | Same; only import paths update |
| `provision/resource.py::ProvisioningResource` | `infrastructure/resource.py::ProvisioningResource` | Thin workspace wrapper around a folder path; asset copying stays on `BlockRepository` |
| `ports/interface.py::_SecretsAdapter` | `infrastructure/secrets.py::SecretsAdapter` | De-privatised; implements `SecretsReader` |
| _(new)_ factories | `infrastructure/__init__.py` | `load_block_repository() -> BlockRepository` and `load_secrets_reader() -> SecretsReader` wire the default adapters |

---

## 4. Key Design Decisions

### D1 — Domain `Block` vs. Infrastructure `SourceBlock`

The current `infrastructure/block.py::Block` is a filesystem-aware object (stores
`folder`, `contract_file`, `terraform_file`, calls `shutil.copytree`). The domain must
not hold filesystem paths.

Solution: introduce a pure domain `Block(id, contract)` entity. The infra layer wraps
it in `SourceBlock(block, source_folder)`. Application commands obtain a
`BlockRepository` from the factory, and asset copying stays behind the repository
boundary via `dump_assets(block_id, target)`.

### D2 — `ProvisioningStep` references domain `Block`, not `SourceBlock`

`ProvisioningStep` moves to `application/services/provisioner/models.py`. Its `block`
field becomes the pure domain `Block` (id + contract). When the orchestration service
needs to copy Terraform assets, it calls `repository.dump_assets(block_id,
target_folder)` — the copy operation is expressed through the repository abstraction,
not by holding a path on the step object.

### D3 — Resolver stays as a module, not a sub-package

`resolver/dag.py`, `resolver/mapper.py`, `resolver/sorter.py` are all pure logic
(no I/O). They are collapsed into `domain/resolver.py`. The sub-package indirection
added no value and made imports noisier.

### D4 — No `ui/` layer

`block` has no Typer commands. Other features call it through `Blocks`. The
`__init__.py` only re-exports `Blocks` and `BlockRef`.

### D5 — `BlockRef` remains a Pydantic `BaseModel`

`BlockRef` is parsed from project manifests (YAML). Keeping it as a Pydantic model
preserves its validation semantics. It moves to `domain/entity.py` but retains the
Pydantic base.

### D6 — `SecretsAdapter` moves from `ports/` to `infrastructure/`

The adapter talks to the `Secrets` feature, which is an external dependency. It is I/O
in the broad sense (crossing feature boundaries). Infrastructure is the right home.

### D7 — Keep `project_name_default` in the contract schema

`project_name_default` is still needed by real block contracts. It remains on
`ConfigField` as part of the block-definition schema, but the policy of when to apply
it stays outside the domain model:
- `application/queries.py` uses the explicit `project_name` argument when building
   manifest defaults.
- `infrastructure/runner.py::VariablesBuilder` uses `project_root.name` when applying
   Terraform variables during provisioning.

---

## 5. Implementation Steps

Steps are ordered so each depends only on already-completed layers.

### Step 1 — domain/
1. Create `domain/__init__.py` with `Layer` enum and `LAYER_ORDER`.
2. Create `domain/value_object.py` with `BlockId`.
3. Create `domain/entity.py` with: `BlockContract` hierarchy (from `contract.py`),
   `Block(id, contract)`, `BlockRef`, `ResolvedBlock`, `OutputReference`.
4. Create `domain/repository.py` with abstract `SecretsReader` and `BlockRepository`.
5. Create `domain/errors.py` consolidating `BlockError` and all resolver errors.
6. Create `domain/resolver.py` with `ProvidesMapper`, `TopologicalSorter`, `DAGResolver`
   (ported from `resolver/mapper.py`, `resolver/sorter.py`, `resolver/dag.py`).

### Step 2 — infrastructure/
1. Create `infrastructure/block.py` with `SourceBlock(block: Block, source_folder: Path)`
   + `dump_assets(target: Path)` method.
2. Create `infrastructure/loader.py` with `FileSystemBlockLoader(BlockRepository)`.
   - `load_all()` / `load_by_ids()` → return `dict[str, Block]` (domain)
   - `dump_assets(block_id, target)` delegates to the underlying `SourceBlock`
3. Create `infrastructure/runner.py` porting `BlockRunner` and `VariablesBuilder`.
   Update import paths to use `domain/entity.py` types.
4. Create `infrastructure/resource.py` porting `ProvisioningResource` as a thin
   workspace-folder helper.
5. Create `infrastructure/secrets.py` with `SecretsAdapter(SecretsReader)`.
6. Create `infrastructure/__init__.py` with `load_block_repository()` and
   `load_secrets_reader()`.

### Step 3 — application/
1. Create `application/queries.py` with `get_manifest_configs()`.
2. Create `application/services/provisioner/` with result dataclasses and
   `BlockProvisioningService` orchestration.
3. Create `application/commands.py` with thin `provision_blocks()` and
   `destroy_blocks()` functions that load repositories/secrets, wire the runner and
   service, delegate, and return.
4. Create `application/interface.py` with `Blocks` façade. It stores only
   `project_root`; methods delegate to `commands` / `queries`.
5. Create `application/__init__.py` re-exporting `Blocks` and the report types.

### Step 4 — package root
1. Create `__init__.py` re-exporting `Blocks` (from application) and `BlockRef`
   (from domain). Remove `SecretsReader` — callers should not depend on it.

### Step 5 — Callers
1. Update `src/freeloader/project/` imports from `block.ports.interface` free functions
   to `block_clean.Blocks` methods or `block_clean.application.*`.
2. Update `tests/` to import from new paths.

### Step 6 — Cut-over
1. Delete the old `block/` directory.
2. Rename `block_clean/` to `block/`.
3. Fix any remaining import strings.
4. Run `uv run pytest` and `uv run ruff check`.

---

## 6. Files Deleted in Old Package

These files have no direct equivalent in the new layout (their logic is redistributed):

| Deleted | Absorbed into |
|---|---|
| `block/base.py` | `domain/value_object.py` + `domain/repository.py` |
| `block/contract.py` | `domain/entity.py` |
| `block/layer.py` | `domain/__init__.py` |
| `block/context.py` | `domain/entity.py` + `application/services/provisioner/service.py` |
| `block/error.py` | `domain/errors.py` |
| `block/facade.py` | `application/interface.py` |
| `block/orchestrator.py` | `application/queries.py` |
| `block/provisioner.py` | `application/commands.py` + `application/services/provisioner/service.py` |
| `block/runner.py` | `infrastructure/runner.py` |
| `block/ports/` | `infrastructure/secrets.py` + `application/interface.py` |
| `block/provision/models.py` | `application/services/provisioner/models.py` |
| `block/provision/resource.py` | `infrastructure/resource.py` |
| `block/resolver/base.py` | `domain/entity.py` |
| `block/resolver/dag.py` | `domain/resolver.py` |
| `block/resolver/mapper.py` | `domain/resolver.py` |
| `block/resolver/sorter.py` | `domain/resolver.py` |
| `block/resolver/error.py` | `domain/errors.py` |
