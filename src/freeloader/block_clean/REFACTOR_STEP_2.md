# Step 2 — Infrastructure Layer

Build all concrete I/O implementations. Every file here may import freely from
`freeloader.block_clean.domain` and from `freeloader.shared`, but **must not import
from `freeloader.block_clean.application`**.

**Prerequisite:** Step 1 (domain) is complete and ruff-clean.

Reference: `docs/FEATURE_ARCHITECTURE.md` §Infrastructure.

---

## Files to Create

```
src/freeloader/block_clean/infrastructure/
├── __init__.py
├── block.py
├── loader.py
├── runner.py
├── resource.py
└── secrets.py
```

---

## Task 2.1 — `infrastructure/block.py`

Introduce `SourceBlock` — the infrastructure-layer wrapper that pairs a domain `Block`
with its filesystem source path. This replaces `block/infrastructure/block.py::Block`
(which conflated domain identity with filesystem concerns).

```python
import shutil
from dataclasses import dataclass
from pathlib import Path

from ..domain.entity import Block


@dataclass(frozen=True)
class SourceBlock:
    block: Block
    source_folder: Path

    def dump_assets(self, target: Path) -> None:
        """Copy Terraform source files from the block's folder into `target`."""
        shutil.copytree(self.source_folder, target, dirs_exist_ok=True)
```

Key differences from the old `Block`:
- No `id` property — use `self.block.id`.
- No `contract` property — use `self.block.contract`.
- No `contract_file` or `terraform_file` fields; these are internal loader concerns.
- `dump_assets` signature changes: it receives the target, not yields itself.

Source: `block/infrastructure/block.py` (restructured).

---

## Task 2.2 — `infrastructure/loader.py`

Implement `FileSystemBlockLoader`, which satisfies the `BlockRepository` ABC from the
domain layer. The loader discovers block folders on disk, builds `SourceBlock` objects
internally, and exposes only pure domain `Block` objects through the repository
interface.

```python
from dataclasses import dataclass
from pathlib import Path

from freeloader.shared import io
from ..domain.entity import Block, BlockContract
from ..domain.repository import BlockRepository
from ..domain.value_object import BlockId

from .block import SourceBlock


@dataclass(frozen=True)
class FileSystemBlockLoader(BlockRepository):
    folder: Path

    @classmethod
    def init(cls, path: Path) -> "FileSystemBlockLoader":
        assert path.is_dir(), f"Blocks root {path} is not a directory"
        return cls(folder=path)

    # ── BlockRepository ABC ──────────────────────────────────────────────────

    def load_all(self) -> dict[str, Block]:
        return {bid: sb.block for bid, sb in self._scan().items()}

    def load_by_ids(self, block_ids: list[BlockId]) -> dict[str, Block]:
        return {str(bid): self._load_source(bid).block for bid in block_ids}

    def dump_assets(self, block_id: BlockId, target: Path) -> None:
        self._load_source(block_id).dump_assets(target)

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _scan(self) -> dict[str, SourceBlock]:
        result: dict[str, SourceBlock] = {}
        for provider_folder in self.folder.iterdir():
            if not provider_folder.is_dir():
                continue
            for block_folder in provider_folder.iterdir():
                if not block_folder.is_dir():
                    continue
                sb = self._source_block_from_folder(block_folder)
                result[str(sb.block.id)] = sb
        return result

    def _load_source(self, block_id: BlockId) -> SourceBlock:
        block_folder = self.folder / block_id.sub_path
        return self._source_block_from_folder(block_folder)

    @staticmethod
    def _source_block_from_folder(folder: Path) -> SourceBlock:
        contract_file = folder / "block.yml"
        assert contract_file.exists(), f"Contract file not found in {folder}"
        assert (folder / "main.tf").exists(), f"Terraform file not found in {folder}"

        block_name = folder.name
        provider_name = folder.parent.name
        block_id = BlockId(f"{provider_name}.{block_name}")

        # Normalise grouped YAML config format before Pydantic validation.
        # The YAML may use {basic: [...], advanced: [...], secrets: [...]} for
        # readability; the domain model only understands the canonical flat list.
        raw = io.load_yaml(contract_file)
        if isinstance(raw.get("config"), dict):
            flat: list[dict] = []
            for group_name in ("basic", "advanced", "secrets"):
                for entry in raw["config"].get(group_name) or []:
                    entry["group"] = group_name
                    flat.append(entry)
            raw["config"] = flat
        contract = BlockContract.model_validate(raw)

        return SourceBlock(
            block=Block(id=block_id, contract=contract),
            source_folder=folder,
        )
```

Source: `block/infrastructure/loader.py` (restructured).

---

## Task 2.3 — `infrastructure/runner.py`

Port `BlockRunner` and `VariablesBuilder` from `block/runner.py`. Update all import
paths to `domain/` types. No logic changes except:
- `run_init` and `run_init_with_deps` collapse into a single `run_init` that
  accepts an optional `extra_vars` dict — the caller (application commands) is
  responsible for resolving dependency inputs before calling the runner.
- `VariablesBuilder.build()` accepts `extra_vars: dict[str, ConfigValue | None] | None`
  instead of `ExecutionContext`. Tfvar name computation (`req_key.replace(".", "_")`)
  is now done by the application's `_resolve_inputs` helper (Step 3).
- Keep the `project_name_default` branch in `VariablesBuilder`. The flag remains on
    `ConfigField`, and provisioning still needs the old behavior of defaulting those
    fields from `project_path.name` when the caller omitted them.

```python
from pathlib import Path

from freeloader.shared.terraform import TerraformResource
from freeloader.shared.types import ConfigValue

from ..domain.entity import ResolvedBlock
from ..domain.repository import SecretsReader

from .resource import ProvisioningResource


class BlockRunner:
    def __init__(self, project_path: Path, secrets: SecretsReader) -> None:
        self._variables_builder = VariablesBuilder(project_path, secrets)

    def run_init(
        self,
        resource: ProvisioningResource,
        block: ResolvedBlock,
        extra_vars: dict[str, ConfigValue | None] | None = None,
    ) -> None:
        tfvars = self._variables_builder.build(block, extra_vars)
        TerraformResource(resource.folder).init(tfvars)

    def run_plan(self, resource: ProvisioningResource) -> None:
        TerraformResource(resource.folder).plan()

    def run_apply(self, resource: ProvisioningResource) -> dict[str, ConfigValue | None]:
        tf = TerraformResource(resource.folder)
        tf.apply()
        return _normalize_outputs(tf.output())

    def run_destroy(self, resource: ProvisioningResource) -> None:
        TerraformResource(resource.folder).destroy()


def _normalize_outputs(raw: dict | list) -> dict[str, ConfigValue | None]:
    if isinstance(raw, list) or not raw:
        return {}
    result: dict[str, ConfigValue | None] = {}
    for key, entry in raw.items():
        result[key] = entry["value"] if isinstance(entry, dict) and "value" in entry else entry
    return result


class VariablesBuilder:
    def __init__(self, project_path: Path, secrets_reader: SecretsReader) -> None:
        self._project_path = project_path
        self._secrets_reader = secrets_reader

    def build(
        self,
        block: ResolvedBlock,
        extra_vars: dict[str, ConfigValue | None] | None = None,
    ) -> dict[str, ConfigValue | None]:
        tfvars: dict[str, ConfigValue | None] = dict(block.ref.config)

        secret_fields = block.contract.config_fields("secrets")
        if secret_fields:
            secret_names = [f.name for f in secret_fields]
            tfvars.update(self._secrets_reader.read(secret_names))

        if extra_vars:
            tfvars.update(extra_vars)

        has_target_folder = any(f.name == "target_folder" for f in block.contract.config)
        if has_target_folder and "target_folder" not in tfvars and self._project_path is not None:
            tfvars["target_folder"] = str(self._project_path)

        if self._project_path is not None:
            for field in block.contract.config:
                if field.project_name_default and field.name not in tfvars:
                    tfvars[field.name] = self._project_path.name

        return tfvars
```

Source: `block/runner.py` — logic is identical, imports are updated.

---

## Task 2.4 — `infrastructure/resource.py`

Implement **`ProvisioningResource`** — an ephemeral Terraform workspace for one
block during a provisioning run. Step 3 constructs it directly as
`ProvisioningResource(folder)`, so no factory class-method is needed.

```python
from pathlib import Path
from shutil import rmtree

class ProvisioningResource:
    """Ephemeral Terraform workspace directory for one block during provisioning."""

    def __init__(self, folder: Path) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        self._folder = folder

    @property
    def folder(self) -> Path:
        return self._folder

    def rm(self) -> None:
        if self._folder.is_dir():
            rmtree(self._folder)
```

Source: `block/provision/resource.py` (restructured). The `from_block` class-method
is dropped — callers construct `ProvisioningResource(folder)` directly. Asset copying
is performed through `BlockRepository.dump_assets(...)`, so `resource.py` does not
need to know about `SourceBlock`.

---

## Task 2.5 — `infrastructure/secrets.py`

Port `_SecretsAdapter` from `block/ports/interface.py`. De-privatise the class
(remove the leading `_`). It implements the domain `SecretsReader` ABC, and
delegates to the `Secrets` application facade from the `secrets` feature.

```python
from dataclasses import dataclass, field

from freeloader.secrets.application.interface import Secrets

from ..domain.repository import SecretsReader


@dataclass(frozen=True)
class SecretsAdapter(SecretsReader):
    secrets: Secrets = field(default_factory=Secrets.for_default_namespace)

    def has_secrets(self, secret_names: list[str]) -> bool:
        return self.secrets.has_secrets(secret_names)

    def read(self, secret_names: list[str]) -> dict[str, str]:
        return self.secrets.read_secrets(secret_names)
```

Note: the old code used `Secrets.for_default_namespace()` as a default field value
directly. Use `field(default_factory=...)` to be safe with frozen dataclasses and
mutable defaults.

Source: `block/ports/interface.py::_SecretsAdapter`.

---

## Task 2.6 — `infrastructure/__init__.py`

Expose two factory functions — one for block definitions and one for the default
secrets reader. Nothing else is re-exported.

```python
import os
from pathlib import Path

from ..domain.repository import BlockRepository, SecretsReader

from .loader import FileSystemBlockLoader
from .secrets import SecretsAdapter


def load_block_repository() -> BlockRepository:
    """Wire a FileSystemBlockLoader from the FREELOADER_BLOCKS env variable."""
    blocks_root = os.getenv("FREELOADER_BLOCKS")
    assert blocks_root, "FREELOADER_BLOCKS environment variable must be set"
    path = Path(blocks_root)
    assert path.is_dir(), f"Blocks root does not exist: {path}"
    return FileSystemBlockLoader.init(path)


def load_secrets_reader() -> SecretsReader:
    """Wire the default SecretsReader for block operations."""
    return SecretsAdapter()
```

`load_block_repository` reads from the environment so application code stays
environment-agnostic. `load_secrets_reader` centralizes the default cross-feature
secrets wiring so application command/query signatures can stay primitive-only.

---

## Verification

After completing all tasks in this step, confirm:

1. `uv run ruff check src/freeloader/block_clean/infrastructure/` reports no errors.
2. None of the infrastructure files import from `freeloader.block_clean.application`.
3. None import from `freeloader.block` (the old package).
4. `SourceBlock`, `FileSystemBlockLoader`, `BlockRunner`, `ProvisioningResource`,
   and `SecretsAdapter` all import cleanly in a Python REPL.
5. `FileSystemBlockLoader` passes an `isinstance` check against `BlockRepository`.
6. `SecretsAdapter` passes an `isinstance` check against `SecretsReader`.
