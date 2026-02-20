# Terraform Package — Facade Refactoring Design

## Current State

```
shared/terraform/
├── __init__.py     (empty)
├── variable.py     TerraformVariable dataclass
├── file.py         TerraformFile + TerraformOutput + parse helpers
├── resource.py     TerraformResource — lifecycle (prepare/create/read/remove)
└── runner.py       TerraformRunner — raw CLI wrapper (init/plan/apply/output/destroy)
```

### Problems

1. **Empty `__init__.py`** — no public API boundary. Every caller picks its own import depth.
2. **`BlockRunner` bypasses `TerraformResource`** — the architecture spec imports `TerraformRunner` directly, skipping the lifecycle abstraction.
3. **`TerraformFile` is caller-visible** — `TerraformResource.prepare()` accepts a `TerraformFile` instance, forcing callers to construct it.
4. **`TerraformOutput` is exposed but unused** by any external caller.
5. **`TerraformResource` splits lifecycle** into `prepare → create → read → remove`; `BlockRunner` needs `prepare → apply → output → destroy` — a naming mismatch that encourages bypass.

---

## Callers

### `shared/block/runner.py` — `BlockRunner`

Primary caller. Per block execution:

```
1. Copy block's main.tf into work dir
2. terraform init
3. terraform apply  ←  tfvars built in-memory from: config + secrets + port outputs
4. terraform output  →  store in ExecutionContext
5. (on destroy) terraform destroy
```

`BlockRunner` does **not** need to inspect tf variables — the `BlockContract` (from `block.yml`) is the SSOT for config field declarations. Variable inspection of `main.tf` is only relevant for tooling (e.g., future `freeloader block validate`).

### `project/usecases/destroy.py` — `ManagedProject.destroy()`

Needs only `destroy()` against an already-initialised work dir.

---

## Target State

### New module: `facade.py`

```python
from pathlib import Path
from typing import Union

from .file import TerraformFile
from .resource import TerraformResource
from .variable import TerraformVariable


class Terraform:
    def __init__(self, root: Path) -> None: ...

    def variables(self, template: Path) -> list[TerraformVariable]: ...
    def prepare(self, template: Path, variables: dict[str, str | list | dict]) -> None: ...
    def apply(self, *, timeout: int | None = None) -> None: ...
    def output(self) -> Union[dict, list]: ...
    def destroy(self, *, timeout: int | None = None) -> None: ...
```

`Terraform(root)` owns one `TerraformResource` internally.  
`variables(template)` wraps `TerraformFile(template).variables` without exposing the class.  
`prepare()` accepts a raw `Path`; constructs `TerraformFile` internally before delegating to `TerraformResource.prepare()`.

### Updated `__init__.py`

```python
from .facade import Terraform
from .variable import TerraformVariable

__all__ = ["Terraform", "TerraformVariable"]
```

Two exported symbols. Everything else is private.

---

## API Mapping

| Old call-site                                    | Facade equivalent                              |
|--------------------------------------------------|------------------------------------------------|
| `TerraformFile(path).variables`                  | `Terraform(root).variables(path)`              |
| `TerraformResource(root).prepare(tf_file, vars)` | `Terraform(root).prepare(template_path, vars)` |
| `TerraformResource(root).create(timeout=t)`      | `Terraform(root).apply(timeout=t)`             |
| `TerraformResource(root).read()`                 | `Terraform(root).output()`                     |
| `TerraformResource(root).remove(timeout=t)`      | `Terraform(root).destroy(timeout=t)`           |
| `TerraformRunner(root).destroy()`                | `Terraform(root).destroy()`                    |

---

## BlockRunner Usage (post-refactor)

```python
from freeloader.shared.terraform import Terraform

class BlockRunner:
    def run_one(self, block: ResolvedBlock, context: ExecutionContext) -> None:
        tf = Terraform(self._block_work_dir(block.ref.resolved_id))
        tfvars = self._build_tfvars(block, context)
        tf.prepare(self._template_path(block), tfvars)
        tf.apply()
        outputs = tf.output()
        context.set_outputs(block.ref.resolved_id, block.contract.map_outputs(outputs))

    def destroy_one(self, block: ResolvedBlock) -> None:
        tf = Terraform(self._block_work_dir(block.ref.resolved_id))
        tf.destroy()
```

---

## Hidden Internals

| Class / symbol     | Visibility after refactor |
|--------------------|---------------------------|
| `TerraformRunner`  | private (`runner.py`)     |
| `TerraformFile`    | private (`file.py`)       |
| `TerraformOutput`  | private (`file.py`)       |
| `TerraformResource`| private (`resource.py`)   |
| `MAIN_FILE`        | private                   |
| `PLAN_FILE`        | private                   |
| `TFVARS_FILE`      | private                   |
| `_parse_variables` | private                   |
| `_parse_outputs`   | private                   |

---

## File Layout (post-refactor)

```
shared/terraform/
├── __init__.py     Exports: Terraform, TerraformVariable
├── facade.py       Terraform  ← new
├── variable.py     TerraformVariable  (unchanged)
├── file.py         TerraformFile, TerraformOutput  (private, unchanged)
├── resource.py     TerraformResource  (private, unchanged)
└── runner.py       TerraformRunner  (private, unchanged)
```

No internal modules are modified. The facade is a pure composition layer.
