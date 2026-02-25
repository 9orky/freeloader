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
from typing import Any
from pydantic import BaseModel, model_validator
from .models import Layer, PortSpec, ConfigField


class BlockMeta(BaseModel):
    description: str = ""
    layer: Layer


class BlockContract(BaseModel):
    block: BlockMeta
    provides: dict[str, PortSpec] = {}
    requires: dict[str, PortSpec] = {}
    config: list[ConfigField] = []

    # model_validator flattens the YAML config dict {basic: [...], advanced: [...], secrets: [...]}
    # into a flat list[ConfigField], stamping each entry with its group name.

    def map_outputs(self, raw: dict[str, Any]) -> dict[str, Any]:
        # Unwraps terraform JSON output envelope: {"value": ..., "type": ...} → bare value.
        ...

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
import heapq
from dataclasses import dataclass
from typing import TYPE_CHECKING
from .config import BlockContract
from .models import LAYER_ORDER

if TYPE_CHECKING:
    from freeloader.project.metadata.manifest import BlockRef


@dataclass(frozen=True)
class ResolvedBlock:
    ref: "BlockRef"
    contract: BlockContract
    inputs: dict[str, str]


class DAGError(Exception): ...
class MissingRequirement(DAGError): ...
class AmbiguousProvider(DAGError): ...
class CircularDependency(DAGError): ...
class DuplicateBlockId(DAGError): ...


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
        contracts: dict[str, BlockContract],
    ) -> dict[str, int]:
        # Uses a min-heap keyed on (layer_priority, original_index) as tiebreaker.
        ...
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
from typing import Any, Callable, Protocol, TypeAlias, runtime_checkable
from .context import ExecutionContext
from .dag import ResolvedBlock


@runtime_checkable
class TerraformProtocol(Protocol):
    def prepare(self, template: Path, variables: dict[str, str | list[str] | dict[str, str]]) -> None: ...
    def apply(self, *, timeout: int | None = None) -> None: ...
    def output(self) -> dict[str, object] | list[object]: ...
    def destroy(self, *, timeout: int | None = None) -> None: ...


# Callable[[namespace, secret_names], {name: value}] — matches secrets.ports.interface.read_secrets
SecretsReader: TypeAlias = Callable[[str, list[str]], dict[str, str]]
# Callable[[work_dir], TerraformProtocol] — wire in freeloader.shared.terraform.Terraform
TerraformFactory: TypeAlias = Callable[[Path], TerraformProtocol]


class BlockRunner:
    def __init__(
        self,
        work_dir: Path,
        blocks_root: Path,
        secrets_reader: SecretsReader,
        terraform_factory: TerraformFactory,
        project_path: Path | None = None,
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
from .dag import DAGError, MissingRequirement, AmbiguousProvider, CircularDependency, DuplicateBlockId
from .runner import BlockRunner

__all__ = [
    "BlockRunner",
    "DAGError",
    "MissingRequirement",
    "AmbiguousProvider",
    "CircularDependency",
    "DuplicateBlockId",
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

### Terraform — injected factory, not direct import
`freeloader.shared.terraform` exposes exactly two symbols: `Terraform` and `TerraformVariable`. `Terraform` satisfies `TerraformProtocol` and is the **only** entry point for all Terraform operations. Direct use of `TerraformRunner`, `TerraformFile`, or `TerraformResource` from their internal modules is forbidden.

`BlockRunner` receives a `TerraformFactory` (`Callable[[Path], TerraformProtocol]`) at construction time — it never imports `Terraform` directly. Callers wire in the concrete class:

```python
from freeloader.shared.terraform import Terraform
runner = BlockRunner(..., terraform_factory=Terraform)
```

Internally `BlockRunner` calls:

```python
tf = self._terraform_factory(self._block_work_dir(block.ref.resolved_id))
tf.prepare(template_path, tfvars)   # copies main.tf, init, plan
tf.apply()                          # apply
outputs = tf.output()               # output -json
# or
tf.destroy()                        # destroy
```

Variable inspection (e.g., for validation tooling) is done outside `BlockRunner`, directly through the facade:

```python
variables: list[TerraformVariable] = Terraform(work_dir).variables(template_path)
```

### Secrets — inter-feature port, not direct vault access
`BlockRunner` receives a `SecretsReader` (`Callable[[str, list[str]], dict[str, str]]`) at construction time. Callers wire in `secrets.ports.interface.read_secrets`:

```python
from freeloader.secrets.ports.interface import read_secrets
runner = BlockRunner(..., secrets_reader=read_secrets)
```

`shared/block` imports nothing from `freeloader.secrets` — dependency inversion keeps the subpackage independent.
