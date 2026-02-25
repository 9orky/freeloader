# Provision Feature — Implementation Plan

> Target: make `fl project provision` fully functional end-to-end.
> Entrypoint: `src/freeloader/project/usecases/provision.py`.
> Current state: empty stub (`pass`).

---

## 1. Current State Inventory

### What exists

| Module | Status |
|---|---|
| `shared/block/dag.py` — `DAGResolver`, `ResolvedBlock`, error types | Complete |
| `shared/block/context.py` — `ExecutionContext` | Complete |
| `shared/block/contract.py` — `BlockContract`, `BlockMeta`, `ConfigField`, `ConfigBuilder` | Complete |
| `shared/block/base.py` — `Block`, `BlockProvider`, `BlockRepository` | Complete (needs trim, see §2.1) |
| `shared/block/runner.py` — `BlockRunner` | Exists but wrong interface (see §2.2) |
| `shared/block/layer.py` — `Layer`, `LAYER_ORDER` | Complete |
| `shared/terraform/facade.py` — `Terraform` | Complete |
| `secrets/ports/interface.py` — `read_secrets` | Complete |
| `project/usecases/user/manifest.py` — `ProjectManifest`, `ManifestContract` | Exists; `load()` discards parsed data (see §2.3) |
| `project/usecases/user/project.py` — `UserProject` | Complete |
| `project/usecases/system/managed_project.py` — `ManagedProject` | Complete |
| `project/usecases/provision.py` | Empty stub |

### What is missing

- `BlockLoader` class (spec §05-Architecture) — currently the contract-loading logic is split across `Block.contract` property and `BlockRepository`; there is no single `load_all() -> dict[str, BlockContract]` entry point.
- `TerraformProtocol` Protocol and `SecretsReader`/`TerraformFactory` type aliases in `runner.py`.
- Wire-up code in `provision.py` that connects all the above pieces.

---

## 2. Required Changes

### 2.1 `shared/block/base.py` — Remove ABCs

`TerraformBridge` and `SecretsBridge` ABCs are dead code: the spec replaces them with injectable callables in `runner.py`. Remove both classes. No callers use them yet.

```
# DELETE from base.py:
class TerraformBridge(ABC): ...
class SecretsBridge(ABC): ...
```

### 2.2 `shared/block/runner.py` — Fix to factory/callable injection

The current constructor takes `secrets_bridge: SecretsBridge` and `terraform_bridge: TerraformBridge`. The spec mandates two injectable callables so the runner stays isolated from concrete imports.

**Required new signature:**

```python
from typing import Any, Callable, Protocol, TypeAlias, runtime_checkable

@runtime_checkable
class TerraformProtocol(Protocol):
    def prepare(self, template: Path, variables: dict[str, str | list[str] | dict[str, str]]) -> None: ...
    def apply(self, *, timeout: int | None = None) -> None: ...
    def output(self) -> dict[str, object] | list[object]: ...
    def destroy(self, *, timeout: int | None = None) -> None: ...

SecretsReader: TypeAlias = Callable[[str, list[str]], dict[str, str]]
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
```

**Required fix in `run_one`:**

Currently `run_one` holds a reference to `self._terraform_bridge` and calls `prepare`/`apply` on it. It must instead call the factory per block:

```python
def run_one(self, block: ResolvedBlock, context: ExecutionContext) -> None:
    tfvars = self._build_tfvars(block, context)
    template = self._blocks_root / block.ref.use / "main.tf"
    work_dir = self._block_work_dir(block.ref.resolved_id)
    tf = self._terraform_factory(work_dir)          # <- factory call
    tf.prepare(template, tfvars)
    tf.apply()
    raw = tf.output()
    outputs = block.contract.map_outputs(raw if isinstance(raw, dict) else {})
    context.set_outputs(block.ref.resolved_id, outputs)
```

**Required fix in `_build_tfvars`:**

The secrets call currently uses `self._secrets_reader(block.ref.use, ...)`. This is already correct: namespace = `block.ref.use` (e.g., `"gitlab/registry"`), which matches `secrets.ports.interface.read_secrets(namespace, names)`.

### 2.3 `shared/block/` — Add `BlockLoader`

Add a new `loader.py` (or extend `base.py`) exposing:

```python
class BlockLoader:
    def __init__(self, blocks_root: Path) -> None:
        self._root = blocks_root          # env: FREELOADER_BLOCKS

    def load_all(self) -> dict[str, BlockContract]:
        # iterate provider dirs → block dirs → read block.yml
        # key: "{provider}/{block}" (matches BlockRef.use)

    def load(self, block_id: str) -> BlockContract:
        # block_id format: "provider/block"
        # split on "/" → locate folder → read block.yml

    def block_ids(self) -> list[str]:
        # returns all "{provider}/{block}" strings
```

The key format `"provider/block"` must match `BlockRef.use` exactly (e.g., `"gitlab/registry"`).

> Note: `base.py` already has `BlockRepository` → `BlockProvider` → `Block.contract`. `BlockLoader` is a thin wrapper that returns `dict[str, BlockContract]` for DAG consumption, without exposing the `Block` abstraction outside this module.

### 2.4 `project/usecases/user/manifest.py` — Fix `load()`

`ProjectManifest.load()` loads and validates the YAML but then discards the result. The `.blocks` property re-reads from disk on every call.

Fix: keep it lazy (re-read is acceptable), but ensure `load()` asserts the file is parseable before returning the handle. Current behaviour is already an implicit validation check — no code change is strictly required for provisioning, but document this debt.

### 2.5 `shared/block/__init__.py` — Extend exports

```python
from .loader import BlockLoader
from .runner import BlockRunner, TerraformProtocol, SecretsReader, TerraformFactory

__all__ = [
    "BlockLoader",
    "BlockRunner",
    "TerraformProtocol",
    "SecretsReader",
    "TerraformFactory",
    # existing DAG error types ...
]
```

---

## 3. Implement `provision.py`

Full implementation of `def provision(project_path: Path) -> None`.

### Step-by-step logic

```
1. Load manifest
   user_project = UserProject(project_path.name, project_path)
   manifest = user_project.load_manifest()               # ProjectManifest handle
   block_refs = manifest.blocks                           # list[BlockRef]

2. Determine work_dir
   managed = ManagedProject found for project_path        # via ManagedProject.iter_all()
   work_dir = managed.resources_path                      # ~/.freeloader/projects/<name>/resources/

3. Resolve blocks_root
   blocks_root = Path(os.getenv("FREELOADER_BLOCKS"))    # source block templates

4. Load contracts
   loader = BlockLoader(blocks_root)
   contracts = {ref.use: loader.load(ref.use) for ref in block_refs}

5. DAG resolution
   resolver = DAGResolver()
   resolved = resolver.resolve(block_refs, contracts)     # list[ResolvedBlock] in execution order

6. Read project path for target_folder injection
   manifest_meta = manifest  # ProjectManifest has no .meta yet — read from ManifestContract
   project_path_override = <from manifest project.path or project_path>

7. Wire and run
   from freeloader.secrets.ports.interface import read_secrets
   from freeloader.shared.terraform import Terraform

   runner = BlockRunner(
       work_dir=work_dir,
       blocks_root=blocks_root,
       secrets_reader=read_secrets,
       terraform_factory=Terraform,
       project_path=project_path_override,
   )
   context = ExecutionContext()
   runner.run_all(resolved, context)
```

### Missing pieces required by step 2 and step 6

**Step 2 — Find `ManagedProject` for the path:**

`ManagedProject.iter_all()` + `ProjectApplication.get_project()` is the pattern used in `destroy.py` and `list_all.py`. Reuse it:

```python
app = ProjectApplication()
for mp in ManagedProject.iter_all(runtime.projects_folder):
    project = app.get_project(mp.project_id)
    if project.path == str(project_path):
        work_dir = mp.resources_path
        break
else:
    raise ValueError(f"Project at '{project_path}' is not registered")
```

**Step 6 — Read `project.path` from manifest:**

`ProjectManifest` currently exposes only `.blocks`. The `ManifestContract.project` field has `path: str | None`. The manifest handle needs either a `.meta` property or a `.project_path` property:

```python
# In ProjectManifest:
@property
def project_path(self) -> Path | None:
    contract = io.load_yaml_model(self.manifest_file, ManifestContract)
    raw = contract.project.path
    return Path(raw) if raw else None
```

Add this property to `user/manifest.py` (one-line addition, no schema change).

---

## 4. Full File Change List

| File | Action | Summary |
|---|---|---|
| `shared/block/base.py` | Edit | Remove `TerraformBridge`, `SecretsBridge` |
| `shared/block/runner.py` | Rewrite | Replace ABCs with `TerraformProtocol` Protocol + `SecretsReader`/`TerraformFactory` type aliases; fix `run_one` to call factory per block |
| `shared/block/loader.py` | Create | `BlockLoader` with `load_all()`, `load()`, `block_ids()` |
| `shared/block/__init__.py` | Edit | Export `BlockLoader`, `BlockRunner`, type aliases |
| `project/usecases/user/manifest.py` | Edit | Add `project_path: Path | None` property |
| `project/usecases/provision.py` | Implement | Full implementation per §3 |

---

## 5. Implementation Order

Execute in this order to keep the codebase in a green state at every step:

1. **Remove ABCs** from `shared/block/base.py` — no callers, zero risk.
2. **Rewrite `runner.py`** — update constructor + `run_one`; run existing tests.
3. **Create `shared/block/loader.py`** — pure new module; no test breakage.
4. **Update `shared/block/__init__.py`** — extend exports.
5. **Add `project_path` property** to `user/manifest.py`.
6. **Implement `provision.py`** — wire everything together.
7. **Run tests** (`make test` / `uv run pytest`) and fix any regressions.

---

## 6. Edge Cases and Error Handling

| Scenario | Expected behaviour |
|---|---|
| Project not registered (no `ManagedProject`) | Raise `ValueError("Project at '...' is not registered")` — same pattern as `destroy.py` |
| Manifest missing (`freeloader.yaml` absent) | `assert` in `ProjectManifest.load()` raises; CLI wraps in `@handle_cli_error` |
| Block id not found in `FREELOADER_BLOCKS` | `BlockLoader.load()` raises `BlockError` from `base.py` |
| DAG cycle | `DAGResolver` raises `CircularDependency` |
| Missing required port | `DAGResolver` raises `MissingRequirement` |
| Ambiguous port provider | `DAGResolver` raises `AmbiguousProvider` |
| Terraform failure | `Terraform.apply()` raises; propagates up |
| Secret not found | `read_secrets()` raises `KeyError` inside `load_storage().get()` |

All exceptions propagate to `ports/cli.py` which is decorated with `@handle_cli_error`.

---

## 7. Out of Scope (YAGNI)

- Progress reporting / streaming output during Terraform apply.
- Partial provisioning (resume from failed step).
- `--dry-run` flag.
- Destroy-on-failure rollback.
- Parallel block execution (DAG currently enforces serial order).
