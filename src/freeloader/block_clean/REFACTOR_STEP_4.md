# Step 4 — Integration, Cut-over, and Cleanup

Wire the new `block_clean` package into the rest of the codebase, delete the old
`block/` package, rename `block_clean/` to `block/`, and verify everything passes.

**Prerequisite:** Steps 1, 2, and 3 are complete and ruff-clean.

---

## Task 4.1 — Package root `__init__.py`

Create `src/freeloader/block_clean/__init__.py` exposing only what other features need.

```python
from .application.interface import Blocks
from .domain.entity import BlockRef

__all__ = ["Blocks", "BlockRef"]
```

`SecretsReader` is **not** re-exported. The only caller that previously needed it
(`project/infrastructure/block_gateway.py`) will use `Blocks.for_project()` instead
and never reference the abstraction directly.

---

## Task 4.2 — Update `project/infrastructure/block_gateway.py`

This is the only file in the project feature that imports from `block`. Replace the
free-function interface with the `Blocks` facade.

**Current** (`block/ports/interface.py` free functions):
```python
import freeloader.block.ports.interface as block_interface
from freeloader.block import BlockRef
...
block_interface.get_manifest_configs(project_root, stack_dict, full_manifest, project_name)
block_interface.provision_project(project_root, resources_root, block_refs)
block_interface.destroy_project(project_root, resources_root, block_refs)
```

**New** (`Blocks` facade):
```python
from freeloader.block import Blocks, BlockRef
...
facade = Blocks.for_project(project_root)
facade.manifest_configs(stack_dict, full_manifest, project_name)
facade.provision(resources_root, block_refs)
facade.destroy(resources_root, block_refs)
```

### Full updated `block_gateway.py`

```python
import dataclasses
from pathlib import Path

from freeloader.block import Blocks, BlockRef
from freeloader.shared.types import ConfigValue

from ..domain.entities import TechStack
from ..domain.repository import BlockGateway


class BlockSystemGateway(BlockGateway):
    def get_manifest_configs(
        self,
        project_root: Path,
        tech_stack: TechStack,
        full_manifest: bool,
        project_name: str | None,
    ) -> dict[str, dict[str, ConfigValue]]:
        stack_dict = {
            k: v
            for k, v in dataclasses.asdict(tech_stack).items()
            if v is not None
        }
        return Blocks.for_project(project_root).manifest_configs(
            stack_dict, full_manifest, project_name
        )

    def provision(
        self,
        project_root: Path,
        resources_root: Path,
        block_refs: list[BlockRef],
    ) -> None:
        Blocks.for_project(project_root).provision(resources_root, block_refs)

    def destroy(
        self,
        project_root: Path,
        resources_root: Path,
        block_refs: list[BlockRef],
    ) -> None:
        Blocks.for_project(project_root).destroy(resources_root, block_refs)
```

Note: each gateway method constructs a fresh `Blocks.for_project()`. If this proves
expensive (e.g., repeated calls in a hot path), the gateway can cache the facade
keyed by `project_root`, but do not optimise prematurely.

---

## Task 4.3 — Update tests

### `tests/test_block_provisioner.py`

This test file exercises `Provisioner`, `ExecutionContext`, and related types directly.
It must be rewritten to test the new `commands.provision_blocks` / `commands.destroy_blocks`
functions (or the `Provisioner`-equivalent helpers), using the new domain types.

**Import changes required:**

| Old import | New import |
|---|---|
| `from freeloader.block.context import ExecutionContext` | `from freeloader.block.domain.entity import ExecutionContext` |
| `from freeloader.block.contract import BlockContract, BlockMeta` | `from freeloader.block.domain.entity import BlockContract, BlockMeta` |
| `from freeloader.block.layer import Layer` | `from freeloader.block.domain import Layer` |
| `from freeloader.block.provisioner import Provisioner` | No direct equivalent — test `commands.provision_blocks` instead |
| `from freeloader.block.resolver import BlockRef, ResolvedBlock` | `from freeloader.block.domain.entity import BlockRef, ResolvedBlock` |

**Behavioral adaptation:**

The old tests inject a `FakeLoader` and `FakeResolver` directly into `Provisioner`.
In the new architecture, `provision_blocks` calls `load_block_repository()` from the
infrastructure factory and `DAGResolver` from the domain. There are two approaches:

**Option A (preferred) — test via the domain function signatures with fake repository:**

```python
# Replace Provisioner injection pattern with a fake BlockRepository
from freeloader.block.domain.repository import BlockRepository, SecretsReader
from freeloader.block.domain.entity import Block, BlockId, BlockRef, ResolvedBlock, BlockContract, BlockMeta
from freeloader.block.domain import Layer

class FakeBlockRepository(BlockRepository):
    def __init__(self, blocks: dict[str, Block]) -> None:
        self._blocks = blocks

    def load_all(self) -> dict[str, Block]:
        return self._blocks

    def load_by_ids(self, block_ids):
        return {str(bid): self._blocks[str(bid)] for bid in block_ids}

    def dump_assets(self, block_id, target) -> None:
        pass  # no-op in tests
```

Then patch `freeloader.block.infrastructure.load_block_repository` in the test to
return the `FakeBlockRepository`.

**Option B — keep testing `_plan` helper directly** if it is made importable:

```python
from freeloader.block.application.commands import _plan
```

This tests the planning logic without needing Terraform runner side effects.

**Test for `ExecutionContext`** (`test_execution_context_resolves_explicit_input_bindings`)
does not need a Provisioner at all — update imports only:

```python
from freeloader.block.domain.entity import ExecutionContext
```

### `tests/test_blocks.py`

Check which symbols it currently imports and update all `freeloader.block.*` paths to
the new layout. Likely changes:

```python
# Old
from freeloader.block.infrastructure import BlockLoader

# New
from freeloader.block.infrastructure.loader import FileSystemBlockLoader
```

Any test that constructs a `BlockLoader` should construct a `FileSystemBlockLoader`
instead. The interface (`load_all`, `load_by_ids`, `dump_assets`) is the same but the
class name changes.

### `tests/test_project_feature.py`

Import of `BlockRef` changes:

```python
# Old
from freeloader.block import BlockRef

# New — path is the same after cut-over
from freeloader.block import BlockRef
```

No change needed here — `BlockRef` is still re-exported from `block.__init__`.

---

## Task 4.4 — Cut-over: rename the package

Once all the above tasks pass `pytest` and `ruff check`, perform the rename.

```bash
# From repo root
mv src/freeloader/block src/freeloader/block_old
mv src/freeloader/block_clean src/freeloader/block
```

Then remove the old package:

```bash
rm -rf src/freeloader/block_old
```

> **Note:** `block_old/` serves as a rollback point until all tests pass.
> Only delete it after the full test suite is green.

---

## Task 4.5 — Fix residual import strings

After the rename, search for any remaining references to the old internal paths that
may exist in non-Python files (YAML, docs, etc.) or missed Python imports:

```bash
grep -r "freeloader\.block\." src/ tests/ --include="*.py" | \
  grep -v "block\.domain\|block\.application\|block\.infrastructure"
```

Any hit pointing to the old flat-package paths (`block.context`, `block.contract`,
`block.resolver`, `block.provisioner`, `block.facade`, `block.ports`, `block.base`,
`block.layer`, `block.orchestrator`, `block.runner`) must be updated.

Also fix the architecture test if the project contains one that asserts module
boundaries:

```bash
# Check for any architecture test file
grep -r "block" tests/test_architecture.py
```

---

## Task 4.6 — Full validation

Run the complete validation suite:

```bash
uv run ruff check src/ tests/
uv run pytest
```

All tests must pass. Ruff must report zero errors or warnings.

If any test fails due to the `Provisioner`-style injection pattern being gone, prefer
updating the test to use the fake-repository approach (Option A in Task 4.3) rather
than restoring internal class access.

---

## Summary of All Files Created Across All Steps

```
block_clean/                        → becomes block/ after Task 4.4
│
├── __init__.py                     Task 4.1
│
├── domain/
│   ├── __init__.py                 Task 1.1  (Layer, LAYER_ORDER)
│   ├── value_object.py             Task 1.2  (BlockId)
│   ├── entity.py                   Task 1.3  (BlockContract hierarchy, Block,
│   │                                          BlockRef, ResolvedBlock,
│   │                                          ExecutionContext, OutputReference,
│   │                                          ResolvedInput)
│   ├── repository.py               Task 1.4  (SecretsReader, BlockRepository)
│   ├── errors.py                   Task 1.5  (BlockError, DAGError subclasses)
│   └── resolver.py                 Task 1.6  (ProvidesMapper, TopologicalSorter,
│                                              DAGResolver)
│
├── infrastructure/
│   ├── __init__.py                 Task 2.6  (load_block_repository factory)
│   ├── block.py                    Task 2.1  (SourceBlock)
│   ├── loader.py                   Task 2.2  (FileSystemBlockLoader)
│   ├── runner.py                   Task 2.3  (BlockRunner, VariablesBuilder)
│   ├── resource.py                 Task 2.4  (ProvisioningResource)
│   └── secrets.py                  Task 2.5  (SecretsAdapter)
│
└── application/
    ├── __init__.py                 Task 3.4
    ├── interface.py                Task 3.3  (Blocks façade)
    ├── commands.py                 Task 3.2  (result dataclasses,
    │                                          provision_blocks, destroy_blocks)
    └── queries.py                  Task 3.1  (get_manifest_configs)
```

**Old `block/` files deleted** (all absorbed into the above):
`base.py`, `contract.py`, `context.py`, `error.py`, `facade.py`, `layer.py`,
`orchestrator.py`, `provisioner.py`, `runner.py`, `ports/`, `provision/`,
`resolver/`, `infrastructure/`.
