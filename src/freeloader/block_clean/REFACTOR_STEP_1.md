# Step 1 — Domain Layer

Establish the innermost layer of the `block_clean` feature. Every file created here
has **zero imports from `freeloader.block` or `freeloader.block_clean.infrastructure`
or `freeloader.block_clean.application`**. The only acceptable external imports are
the Python standard library and `pydantic` (for `BlockRef`, which is parsed from
project manifests).

Reference: `docs/FEATURE_ARCHITECTURE.md` §Domain.

---

## Files to Create

```
src/freeloader/block_clean/domain/
├── __init__.py
├── value_object.py
├── entity.py
├── repository.py
├── errors.py
└── resolver.py
```

---

## Task 1.1 — `domain/__init__.py`

Port `block/layer.py` verbatim, but place it in the domain package init so it is
importable as `from freeloader.block_clean.domain import Layer, LAYER_ORDER`.

```python
from enum import Enum


class Layer(str, Enum):
    infra = "infra"
    platform = "platform"
    source = "source"
    registry = "registry"
    build = "build"
    deploy = "deploy"
    network = "network"
    data = "data"
    observe = "observe"


LAYER_ORDER: dict[Layer, int] = {layer: i for i, layer in enumerate(Layer)}
```

Source: `block/layer.py`. Delete the source file later in Step 6.

---

## Task 1.2 — `domain/value_object.py`

Port `BlockId` from `block/base.py`. This is the only class in that file that is a
pure value object.

```python
class BlockId(str):
    def __new__(cls, value: str) -> "BlockId":
        if "." not in value:
            raise ValueError(
                f"Invalid block id '{value}', expected format 'provider.block'"
            )
        return str.__new__(cls, value)

    @property
    def provider(self) -> str:
        return self.split(".")[0]

    @property
    def block(self) -> str:
        return self.split(".")[1]

    @property
    def sub_path(self) -> str:
        return f"{self.provider}/{self.block}"
```

Source: `block/base.py::BlockId`.

---

## Task 1.3 — `domain/entity.py`

This file consolidates all pure domain data structures. It draws from four existing
files (`contract.py`, `context.py`, `resolver/base.py`) and adds one new entity.

### 1.3a — Contract types (from `block/contract.py`)

Port all Pydantic models and enums verbatim. The only import updates are:
- `from freeloader.shared.types import ConfigValue` — keep as-is
- `from .__ import Layer` → `from . import Layer`

Classes to include (in order):
- `CostTier(str, Enum)`
- `FreeTierLimit(BaseModel)`
- `BlockCostSpec(BaseModel)`
- `BlockMeta(BaseModel)`
- `ConfigField(BaseModel)` — **keep** `project_name_default: bool = False`.
    This flag is part of the block-contract schema used by real blocks. The domain
    model owns the data shape; application and infrastructure code decide when to
    apply it.
- `PortSpec(BaseModel)`
- `BlockContract(BaseModel)` — keep only `required_secret_keys` and
    `config_fields()` as convenience APIs. **Drop**:
  - `_flatten_config_groups` model validator — YAML format normalisation belongs in
    the infrastructure loader (`FileSystemBlockLoader._source_block_from_folder`,
    Step 2). The domain model only understands the canonical flat list form.
  - `collect_defaults()` method — a policy decision (which groups to include, whether
    to inject the project name) belongs in `application/queries.py` (Step 3).

The internal constant `_TECH_STACK_KEYS` stays in this file.

### 1.3b — New `Block` domain entity

Add the pure domain entity after the contract types. This entity carries only the
minimum needed for the application layer to reason about a block without touching
the filesystem:

```python
from dataclasses import dataclass
from .value_object import BlockId

@dataclass(frozen=True)
class Block:
    id: BlockId
    contract: BlockContract
```

This is **new** — there is no direct counterpart in the old `block/` package at the
domain level. The old `infrastructure/block.py::Block` holds filesystem paths too and
will become `SourceBlock` in infrastructure (Step 2).

### 1.3c — Execution dependency reference (from `block/context.py`)

Port `OutputReference` as a frozen dataclass. **Do not port** `ResolvedInput` or
`ExecutionContext`.

- `ResolvedInput` becomes unnecessary in the refactor; the provisioning service can
    work directly with `{tfvar_name: value}` mappings.
- `ExecutionContext` is a mutable accumulator for the provisioning loop and belongs
    in the provisioning service implementation (Step 3), not in the domain.

**Drop the `tfvar_name` property** from `OutputReference`. Generating a Terraform
variable name by replacing `.` with `_` is a provisioning concern; the application
service performs that translation when preparing `extra_vars` for the runner.

### 1.3d — Resolver reference types (from `block/resolver/base.py`)

Port `BlockRef` and `ResolvedBlock` verbatim. `BlockRef` keeps its `pydantic.BaseModel`
base because it is parsed from YAML manifests. Update imports:
- `from freeloader.shared.types import ConfigValue`
- `from .entity import BlockContract` → same file, no cross-import needed — place
  `BlockRef`/`ResolvedBlock` after the contract classes.

Final import block for `entity.py`:
```python
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal

from pydantic import BaseModel, computed_field

from freeloader.shared.types import ConfigValue

from . import Layer
from .value_object import BlockId
```

(`model_validator` is no longer needed; `_flatten_config_groups` was removed.)

---

## Task 1.4 — `domain/repository.py`

Port `SecretsReader` from `block/base.py` and add `BlockRepository` for block
definition storage.

```python
from abc import ABC, abstractmethod
from pathlib import Path

from .entity import Block
from .value_object import BlockId


class SecretsReader(ABC):
    @abstractmethod
    def has_secrets(self, secret_names: list[str]) -> bool: ...

    @abstractmethod
    def read(self, secret_names: list[str]) -> dict[str, str]: ...


class BlockRepository(ABC):
    """Storage contract for discovering and loading block definitions."""

    @abstractmethod
    def load_all(self) -> dict[str, Block]: ...

    @abstractmethod
    def load_by_ids(self, block_ids: list[BlockId]) -> dict[str, Block]: ...

    @abstractmethod
    def dump_assets(self, block_id: BlockId, target: Path) -> None:
        """Copy the Terraform source files for `block_id` into `target`."""
        ...
```

The `dump_assets` method on `BlockRepository` keeps block-source paths out of the
application layer. The application commands call this method rather than holding a
source `Path` directly.

Source: `block/base.py::SecretsReader`.

---

## Task 1.5 — `domain/errors.py`

Consolidate all domain exceptions from `block/error.py` and `block/resolver/error.py`.

```python
class BlockError(Exception):
    pass


class DAGError(Exception):
    ...


class MissingRequirement(DAGError):
    ...


class AmbiguousProvider(DAGError):
    ...


class CircularDependency(DAGError):
    ...


class DuplicateBlockId(DAGError):
    ...
```

No changes in logic. Sources: `block/error.py`, `block/resolver/error.py`.

---

## Task 1.6 — `domain/resolver.py`

Collapse the three-file sub-package `block/resolver/` into a single module. All three
classes are pure Python logic with no I/O and no filesystem access.

### Imports

```python
import heapq

from . import LAYER_ORDER
from .entity import BlockContract, BlockRef, ResolvedBlock
from .errors import AmbiguousProvider, CircularDependency, MissingRequirement
```

### Classes to include (in order)

**`ProvidesMapper`** — port from `block/resolver/mapper.py`:
```python
class ProvidesMapper:
    def build_map(
        self, block_refs: list[BlockRef], contracts: dict[str, BlockContract]
    ) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {}
        for ref in block_refs:
            contract = contracts[ref.use]
            layer = contract.block.layer.value
            for output_name in contract.provides:
                key = f"{layer}.{output_name}"
                result.setdefault(key, []).append(ref.resolved_id)
        return result
```

**`TopologicalSorter`** — port from `block/resolver/sorter.py` verbatim. The heap
priority tuple is `(layer_priority, original_index, resolved_id)`.

**`DAGResolver`** — port from `block/resolver/dag.py` verbatim. Composes
`ProvidesMapper` and `TopologicalSorter`.

Sources: `block/resolver/mapper.py`, `block/resolver/sorter.py`, `block/resolver/dag.py`.

---

## Verification

After completing all tasks in this step, confirm:

1. `uv run ruff check src/freeloader/block_clean/domain/` reports no errors.
2. None of the domain files import from:
   - `freeloader.block_clean.application`
   - `freeloader.block_clean.infrastructure`
   - `freeloader.block` (old package)
   - `pathlib` (except `repository.py`, for the `dump_assets` signature only)
3. `from freeloader.block_clean.domain import Layer, LAYER_ORDER` works.
4. `from freeloader.block_clean.domain.entity import Block, BlockRef, BlockContract, OutputReference` works.
5. `from freeloader.block_clean.domain.repository import SecretsReader, BlockRepository` works.
6. `from freeloader.block_clean.domain.resolver import DAGResolver` works.
