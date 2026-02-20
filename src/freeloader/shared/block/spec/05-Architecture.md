# Block System — Architecture (`src/freeloader/shared/block/`)

## Package Layout

```
src/freeloader/shared/block/
├── __init__.py      Public API exports.
├── models.py        Pydantic primitives: Layer, PortSpec, ConfigField.
├── config.py        BlockMeta, BlockContract, ConfigBuilder.
├── dag.py           DAGResolver, ResolvedBlock, error types.
├── context.py       ExecutionContext — runtime output accumulator.
├── loader.py        BlockLoader — discovers and parses block.yml files.
└── runner.py        BlockRunner — orchestrates Terraform execution per block.

src/freeloader/project/metadata/
└── manifest.py      BlockRef, ProjectManifest — user manifest schema.
```

---

## Module: `models.py`

Shared Pydantic primitives used across the block package.

```python
from enum import Enum
from typing import Literal
from pydantic import BaseModel


class Layer(str, Enum):
    infra    = "infra"
    platform = "platform"
    source   = "source"
    registry = "registry"
    build    = "build"
    deploy   = "deploy"
    network  = "network"
    data     = "data"
    observe  = "observe"


LAYER_ORDER: dict[Layer, int] = {layer: i for i, layer in enumerate(Layer)}


class PortSpec(BaseModel):
    description: str = ""
    optional: bool = False
    sensitive: bool = False


class ConfigField(BaseModel):
    name: str
    description: str = ""
    required: bool = False
    default: str | int | float | bool | list[str] | None = None
    choices: list[str] | None = None
    group: Literal["basic", "advanced", "secrets"] = "basic"
    project_name_default: bool = False
```

---

## Module: `config.py`

Defines the full block contract and the manifest config builder.

```python
from pathlib import Path
from typing import Any
from pydantic import BaseModel
from .models import Layer, PortSpec, ConfigField


class BlockMeta(BaseModel):
    description: str = ""
    layer: Layer


class BlockContract(BaseModel):
    block: BlockMeta
    provides: dict[str, PortSpec] = {}
    requires: dict[str, PortSpec] = {}
    config: list[ConfigField] = []

    def map_outputs(self, raw: dict[str, Any]) -> dict[str, Any]: ...

    def config_fields(self, group: str) -> list[ConfigField]: ...


class ConfigBuilder:
    def __init__(self, contracts: dict[str, BlockContract]) -> None: ...

    def build(
        self,
        block_id: str,
        project_name: str,
        full: bool = False,
    ) -> dict[str, Any]: ...
```

---

## Module: `dag.py`

Resolves a flat list of block refs into a topologically sorted execution plan.

```python
from collections import defaultdict, deque
from dataclasses import dataclass
from .config import BlockContract
from .models import LAYER_ORDER


@dataclass(frozen=True)
class ResolvedBlock:
    ref: "BlockRef"
    contract: BlockContract
    inputs: dict[str, str]


class DAGError(Exception): ...
class MissingRequirement(DAGError): ...
class AmbiguousProvider(DAGError): ...
class CircularDependency(DAGError): ...


class DAGResolver:
    def resolve(
        self,
        block_refs: list["BlockRef"],
        contracts: dict[str, BlockContract],
    ) -> list[ResolvedBlock]: ...

    def _build_provides_map(
        self,
        block_refs: list["BlockRef"],
        contracts: dict[str, BlockContract],
    ) -> dict[str, list[str]]: ...

    def _topological_sort(
        self,
        block_refs: list["BlockRef"],
        adjacency: dict[str, set[str]],
    ) -> dict[str, int]: ...
```

---

## Module: `context.py`

Accumulates block outputs during a provisioning run. Passed between blocks.

```python
from typing import Any


class ExecutionContext:
    def __init__(self) -> None: ...

    def set_outputs(self, block_id: str, outputs: dict[str, Any]) -> None: ...

    def get_output(self, block_id: str, key: str) -> Any: ...

    def get_all_outputs(self, block_id: str) -> dict[str, Any]: ...

    def has_outputs(self, block_id: str) -> bool: ...

    def resolve_inputs(self, inputs_map: dict[str, str]) -> dict[str, Any]: ...
```

---

## Module: `loader.py`

Discovers and parses `block.yml` files. The registry of available blocks.

```python
from pathlib import Path
from .config import BlockContract


class BlockLoader:
    def __init__(self, blocks_root: Path) -> None: ...

    def load_all(self) -> dict[str, BlockContract]: ...

    def load(self, block_id: str) -> BlockContract: ...

    def _parse(self, path: Path) -> BlockContract: ...

    def block_ids(self) -> list[str]: ...
```

---

## Module: `runner.py`

Orchestrates Terraform execution for each resolved block in order.

```python
from pathlib import Path
from typing import Any
from .config import BlockContract
from .context import ExecutionContext
from .dag import ResolvedBlock
from freeloader.shared.terraform import Terraform
from freeloader.secrets.storage.vault import Vault


class BlockRunner:
    def __init__(
        self,
        work_dir: Path,
        blocks_root: Path,
        vault: Vault,
    ) -> None: ...

    def run_all(
        self,
        blocks: list[ResolvedBlock],
        context: ExecutionContext,
    ) -> None: ...

    def run_one(
        self,
        block: ResolvedBlock,
        context: ExecutionContext,
    ) -> None: ...

    def _build_tfvars(
        self,
        block: ResolvedBlock,
        context: ExecutionContext,
    ) -> dict[str, Any]: ...

    def _block_work_dir(self, resolved_id: str) -> Path: ...
```

---

## Module: `manifest.py` (`src/freeloader/project/metadata/`)

User-facing schema — parsed from `freeloader.yaml`.

```python
from pathlib import Path
from typing import Any
from pydantic import BaseModel, computed_field
from freeloader.shared import yaml_io


class BlockRef(BaseModel):
    use: str
    id: str | None = None
    config: dict[str, Any] = {}

    @computed_field
    @property
    def resolved_id(self) -> str: ...


class ManifestMeta(BaseModel):
    name: str
    description: str = ""
    path: str | None = None


class ProjectManifest(BaseModel):
    project: ManifestMeta
    blocks: list[BlockRef]


def load_manifest(path: Path) -> ProjectManifest: ...
```

---

## Module: `__init__.py`

Public API of the block package.

```python
from .dag import DAGError, MissingRequirement, AmbiguousProvider, CircularDependency
from .runner import BlockRunner

__all__ = [
    "BlockRunner",
    "DAGError",
    "MissingRequirement",
    "AmbiguousProvider",
    "CircularDependency",
]
```

---

## Composition: Full Provisioning Flow

```python
def provision_project(project_path: Path) -> None: ...
```

---

## Design Notes

### State isolation
Each block's Terraform state lives at `.freeloader/state/{resolved_id}/terraform.tfstate`. Terraform runs directly against the block source directory using `-state=<state_path>`, keeping the source clean and avoiding conflicts when two blocks share the same provider.

### Secrets never on disk
The tfvars dict is built in memory and written as `terraform.tfvars.json` with mode `0600` in the block's state directory. The file is deleted immediately after `terraform apply` completes. Secrets are never written to `freeloader.yaml` or any committed file.

### `project.path` and `target_folder`
`project.path` in the manifest is the SSOT for the project's local directory. During `_build_tfvars`, if a block's contract declares a config field named `target_folder` and the user has not overridden it in `config`, the provisioner injects `project.path` automatically.

### Terraform package — single abstraction
`freeloader.shared.terraform` exposes exactly two symbols: `Terraform` and `TerraformVariable`. `Terraform` is the **only** entry point for all Terraform operations within the block system and project usecases. Direct use of `TerraformRunner`, `TerraformFile`, or `TerraformResource` from their internal modules is forbidden. `BlockRunner` constructs one `Terraform(work_dir)` instance per block and calls the full lifecycle through it:

```python
tf = Terraform(self._block_work_dir(block.ref.resolved_id))
tf.prepare(template_path, tfvars)   # copies main.tf, init, plan
tf.apply()                          # apply
outputs = tf.output()               # output -json
# or
tf.destroy()                        # destroy
```

Variable inspection of a template before provisioning (e.g., for validation tooling) is also done through the facade:

```python
variables: list[TerraformVariable] = Terraform(work_dir).variables(template_path)
```
