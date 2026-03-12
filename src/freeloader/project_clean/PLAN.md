# Project Feature — Clean Architecture Migration Plan


Migrate `src/freeloader/project/` to the canonical four-layer feature architecture
documented in `docs/FEATURE_ARCHITECTURE.md`, using `secrets` as the reference
implementation. The target package lives at `src/freeloader/project_clean/` during
the migration and replaces `project/` when complete.

---

## 1. Why This Migration

The current `project` package diverges from the canonical architecture in several ways:

| Problem | Impact |
|---|---|
| `__init__.py` exports nothing | No usable machine API for other features |
| `models.py` at package root | Domain types mixed with package scaffolding |
| `application.py` re-delegates to `usecases/` | Redundant indirection layer |
| No abstract repository contracts | Use cases couple directly to concrete adapters |
| No `infrastructure/interface.py` facade | Other features cannot call `project` cleanly |
| `ManageProjectResult` used as both domain type and CLI shape | Conflates presentation with domain |
| `ManifestContract` inside `adapters/manifest_store.py` | File-format schema buried; not a proper domain entity |

---

## 2. Current Structure Analysis

```
project/
├── __init__.py            # just a docstring; no exports
├── application.py         # thin re-delegation facade to usecases/
├── models.py              # TechStack, ManageProjectResult (Pydantic BaseModel)
├── cli.py                 # project_app (Typer); wired to application.py
├── adapters/
│   ├── block_gateway.py   # wraps freeloader.block.ports.interface
│   ├── manifest_store.py  # YAML I/O + ManifestContract, ManifestMeta, ManifestTechStack
│   └── tech_stack.py      # wraps freeloader.shared.tech.TechFacade.detect_stack()
└── usecases/
    ├── detect.py          # detect_project_stack() → tech_stack_adapter
    ├── manage.py          # manage_project() → detect + get_configs + save_manifest
    ├── provision.py       # provision_project() → load_manifest + provision
    └── forget.py          # forget_project() → load_manifest + destroy + delete
```

### Behavior inventory

| Use case | Reads | Writes |
|---|---|---|
| `detect_project_stack(folder)` | folder filesystem | — |
| `manage_project(name, folder, full_manifest)` | folder filesystem, block registry | `freeloader.yaml`, `.freeloader/` dir |
| `provision_project(folder)` | `freeloader.yaml`, block registry | Terraform state under `.freeloader/` |
| `forget_project(folder)` | `freeloader.yaml`, block registry | removes `freeloader.yaml` + `.freeloader/` |

---

## 3. Target Structure

```
project_clean/
├── __init__.py                # re-exports: project_app, Project
│
├── domain/
│   ├── __init__.py            # (empty)
│   ├── entities.py            # TechStack, Manifest, ManageResult (frozen dataclasses)
│   └── repository.py         # ManifestRepository, TechStackDetector, BlockGateway (ABCs)
│
├── application/
│   ├── __init__.py            # re-exports all public use-case functions (flat surface)
│   ├── commands.py            # manage_project, provision_project, forget_project
│   └── queries.py             # detect_stack, get_manifest
│
├── infrastructure/
│   ├── __init__.py            # factory functions + re-export of Project
│   ├── interface.py           # Project facade (machine API for other features)
│   ├── manifest_store.py      # YamlManifestStore(ManifestRepository)
│   ├── tech_stack.py          # TechFacadeDetector(TechStackDetector)
│   └── block_gateway.py       # BlockSystemGateway(BlockGateway)
│
└── ui/
    ├── __init__.py
    ├── cli.py                 # project_app (Typer); wired to application module
    └── views.py               # ManageProjectView (Pydantic; used only for CLI rendering)
```

---

## 4. File-by-File Migration Map

| Old file | New file | Action |
|---|---|---|
| `models.py` | `domain/entities.py` | Rewrite as frozen dataclasses; split `ManageProjectResult` from `TechStack` |
| `adapters/tech_stack.py` | `infrastructure/tech_stack.py` | Wrap in `TechFacadeDetector(TechStackDetector)` |
| `adapters/manifest_store.py` | `infrastructure/manifest_store.py` | Wrap in `YamlManifestStore(ManifestRepository)`; keep `ManifestContract` as internal file-format schema |
| `adapters/block_gateway.py` | `infrastructure/block_gateway.py` | Wrap in `BlockSystemGateway(BlockGateway)` |
| `usecases/detect.py` | `application/queries.py` | Move `detect_stack()` |
| `usecases/manage.py` | `application/commands.py` | Move `manage_project()`, use factories |
| `usecases/provision.py` | `application/commands.py` | Move `provision_project()`, use factories |
| `usecases/forget.py` | `application/commands.py` | Move `forget_project()`, use factories |
| `cli.py` | `ui/cli.py` | Move; rewire to `from .. import application` |
| `application.py` | _(deleted)_ | Redundant delegation layer removed |
| _(new)_ | `domain/repository.py` | Abstract contracts for all three external dependencies |
| _(new)_ | `infrastructure/interface.py` | `Project` facade class |
| _(new)_ | `ui/views.py` | `ManageProjectView` for CLI serialization |
| `__init__.py` | `__init__.py` | Proper re-exports: `project_app`, `Project` |

---

## 5. Domain Layer (`domain/`)

### `domain/entities.py`

```python
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from freeloader.shared.types import ConfigValue
from freeloader.block import BlockRef          # acceptable: block is a lower-level subsystem

@dataclass(frozen=True)
class TechStack:
    language: str | None = None
    language_version: str | None = None
    package_manager: str | None = None
    framework: str | None = None

@dataclass(frozen=True)
class Manifest:
    name: str
    tech_stack: TechStack
    block_refs: tuple[BlockRef, ...]

@dataclass(frozen=True)
class ManageResult:
    tech_stack: TechStack
    block_configs: dict[str, dict[str, ConfigValue]]
```

**Design notes:**
- `TechStack` switches from Pydantic `BaseModel` to a frozen dataclass. No validation
  logic is lost; the existing fields had no validators.
- `Manifest` replaces `ManifestContract` as the domain view of a loaded manifest.
  `ManifestContract` (the YAML file schema with `ManifestMeta`, `ManifestTechStack`)
  stays private inside `infrastructure/manifest_store.py`.
- `ManageResult` replaces `ManageProjectResult`. It is a domain result value, not a
  presentation shape. The CLI converts it to `ManageProjectView` for display.
- `BlockRef` is imported from `freeloader.block` — not redefined. `block` is a
  subsystem at a lower level than project features.

### `domain/repository.py`

```python
import abc
from pathlib import Path
from freeloader.shared.types import ConfigValue
from freeloader.block import BlockRef
from .entities import TechStack, Manifest

class ManifestRepository(abc.ABC):
    @abc.abstractmethod
    def exists(self, folder: Path) -> bool: ...
    @abc.abstractmethod
    def load(self, folder: Path) -> Manifest: ...
    @abc.abstractmethod
    def save(self, name: str, folder: Path,
             tech_stack: TechStack,
             block_configs: dict[str, dict[str, ConfigValue]]) -> None: ...
    @abc.abstractmethod
    def delete(self, folder: Path) -> None: ...
    @abc.abstractmethod
    def resources_folder(self, folder: Path) -> Path: ...

class TechStackDetector(abc.ABC):
    @abc.abstractmethod
    def detect(self, folder: Path) -> TechStack | None: ...

class BlockGateway(abc.ABC):
    @abc.abstractmethod
    def get_manifest_configs(
        self, project_root: Path, tech_stack: TechStack,
        full_manifest: bool, project_name: str | None
    ) -> dict[str, dict[str, ConfigValue]]: ...
    @abc.abstractmethod
    def provision(self, project_root: Path, resources_root: Path,
                  block_refs: list[BlockRef]) -> None: ...
    @abc.abstractmethod
    def destroy(self, project_root: Path, resources_root: Path,
                block_refs: list[BlockRef]) -> None: ...
```

---

## 6. Application Layer (`application/`)

### `application/commands.py`

Each function obtains its dependencies through the infrastructure factories. No I/O,
no CLI types, no Pydantic. Returns domain entities or `None`.

```python
from pathlib import Path
from ..infrastructure import load_manifest_repository, load_tech_stack_detector, load_block_gateway
from ..domain.entities import TechStack, ManageResult

def manage_project(name: str, folder: Path, full_manifest: bool = False) -> ManageResult:
    manifest_repo = load_manifest_repository()
    detector = load_tech_stack_detector()
    block_gw = load_block_gateway()

    assert folder.is_dir(), f"{folder} is not a directory"
    assert not manifest_repo.exists(folder), "Manifest already exists"

    tech_stack = detector.detect(folder) or TechStack()
    block_configs = block_gw.get_manifest_configs(folder, tech_stack, full_manifest, name)
    manifest_repo.save(name, folder, tech_stack, block_configs)
    return ManageResult(tech_stack=tech_stack, block_configs=block_configs)

def provision_project(folder: Path) -> None:
    manifest_repo = load_manifest_repository()
    block_gw = load_block_gateway()
    manifest = manifest_repo.load(folder)
    block_gw.provision(folder, manifest_repo.resources_folder(folder), list(manifest.block_refs))

def forget_project(folder: Path) -> None:
    manifest_repo = load_manifest_repository()
    block_gw = load_block_gateway()
    manifest = manifest_repo.load(folder)
    block_gw.destroy(folder, manifest_repo.resources_folder(folder), list(manifest.block_refs))
    manifest_repo.delete(folder)
```

### `application/queries.py`

```python
from pathlib import Path
from ..infrastructure import load_manifest_repository, load_tech_stack_detector
from ..domain.entities import TechStack, Manifest

def detect_stack(folder: Path) -> TechStack | None:
    return load_tech_stack_detector().detect(folder)

def get_manifest(folder: Path) -> Manifest:
    return load_manifest_repository().load(folder)
```

### `application/__init__.py`

Re-exports all public use-case functions so `cli.py` can do `from .. import application`
and call `application.manage_project(...)` without knowing about submodules.

```python
from .commands import manage_project, provision_project, forget_project
from .queries import detect_stack, get_manifest

__all__ = ["manage_project", "provision_project", "forget_project",
           "detect_stack", "get_manifest"]
```

---

## 7. Infrastructure Layer (`infrastructure/`)

### `infrastructure/manifest_store.py`

`YamlManifestStore` implements `ManifestRepository`. Internally keeps `ManifestContract`,
`ManifestMeta`, `ManifestTechStack` as private file-format schemas (unchanged from
current `adapters/manifest_store.py`). Converts between file-format types and domain
types at the load/save boundary.

Key conversion points:
- `load()` → reads YAML into `ManifestContract`, converts to `Manifest` (domain entity)
- `save()` → converts `TechStack` and `block_configs` to `ManifestContract`, writes YAML

```python
class YamlManifestStore(ManifestRepository):
    _FILE_NAME = "freeloader.yaml"

    def exists(self, folder): ...
    def load(self, folder) -> Manifest: ...     # converts ManifestContract → Manifest
    def save(self, name, folder, tech_stack, block_configs): ...
    def delete(self, folder): ...
    def resources_folder(self, folder) -> Path: ...
```

### `infrastructure/tech_stack.py`

```python
class TechFacadeDetector(TechStackDetector):
    def detect(self, folder: Path) -> TechStack | None:
        from freeloader.shared.tech import TechFacade
        detected = TechFacade().detect_stack(folder)
        if not detected:
            return None
        return TechStack(**detected)
```

### `infrastructure/block_gateway.py`

```python
class BlockSystemGateway(BlockGateway):
    def get_manifest_configs(self, project_root, tech_stack, full_manifest, project_name):
        import freeloader.block.ports.interface as block_interface
        stack_data = dataclasses.asdict(tech_stack)
        return block_interface.get_manifest_configs(project_root, stack_data, full_manifest, project_name)

    def provision(self, project_root, resources_root, block_refs):
        import freeloader.block.ports.interface as block_interface
        block_interface.provision_project(project_root, resources_root, block_refs)

    def destroy(self, project_root, resources_root, block_refs):
        import freeloader.block.ports.interface as block_interface
        block_interface.destroy_project(project_root, resources_root, block_refs)
```

### `infrastructure/interface.py`

```python
from dataclasses import dataclass
from pathlib import Path
from ..application import commands, queries
from ..domain.entities import TechStack, ManageResult

@dataclass(frozen=True)
class Project:
    project_folder: Path

    def detect_stack(self) -> TechStack | None:
        return queries.detect_stack(self.project_folder)

    def manage(self, name: str, full_manifest: bool = False) -> ManageResult:
        return commands.manage_project(name, self.project_folder, full_manifest)

    def provision(self) -> None:
        commands.provision_project(self.project_folder)

    def forget(self) -> None:
        commands.forget_project(self.project_folder)

    @classmethod
    def for_current_directory(cls) -> "Project":
        return cls(project_folder=Path.cwd())
```

### `infrastructure/__init__.py`

```python
from ..domain.repository import ManifestRepository, TechStackDetector, BlockGateway
from .interface import Project
from .manifest_store import YamlManifestStore
from .tech_stack import TechFacadeDetector
from .block_gateway import BlockSystemGateway

def load_manifest_repository() -> ManifestRepository:
    return YamlManifestStore()

def load_tech_stack_detector() -> TechStackDetector:
    return TechFacadeDetector()

def load_block_gateway() -> BlockGateway:
    return BlockSystemGateway()

__all__ = ["load_manifest_repository", "load_tech_stack_detector",
           "load_block_gateway", "Project"]
```

---

## 8. UI Layer (`ui/`)

### `ui/views.py`

```python
from pydantic import BaseModel, Field
from freeloader.shared.types import ConfigValue

class ManageProjectView(BaseModel):
    tech_stack: dict | None = None
    block_configs: dict[str, dict[str, ConfigValue]] = Field(default_factory=dict)
```

Used only in `ui/cli.py` to convert `ManageResult` into a dict for `console.print_dict()`.

### `ui/cli.py`

```python
import dataclasses
from pathlib import Path
import typer
from freeloader.shared import console
from .. import application
from .views import ManageProjectView

project_app = typer.Typer(
    name="project",
    help="Manage project manifests and provisioning",
    no_args_is_help=True,
)

def _cwd() -> Path:
    return Path.cwd()

@project_app.command(help="Detect the technology stack for the current project")
@console.handle_errors
def detect() -> None:
    tech_stack = application.detect_stack(_cwd())
    if tech_stack and tech_stack.language:
        console.print_dict(dataclasses.asdict(tech_stack))
        return
    console.warn("Could not detect technology stack for this project.")

@project_app.command(help="Generate a project manifest for the current directory")
@console.handle_errors
def manage(
    full_manifest: bool = typer.Option(False, "--full-manifest",
        help="Include advanced configuration fields in the manifest"),
) -> None:
    cwd = _cwd()
    result = application.manage_project(cwd.name, cwd, full_manifest)
    view = ManageProjectView(
        tech_stack=dataclasses.asdict(result.tech_stack),
        block_configs=result.block_configs,
    )
    console.print_dict(view.model_dump(mode="python"))

@project_app.command(help="Provision project resources from the current manifest")
@console.handle_errors
def provision() -> None:
    cwd = _cwd()
    application.provision_project(cwd)
    console.ok(f"Project '{cwd.name}' provisioned successfully.")

@project_app.command(help="Destroy project resources and remove local state")
@console.handle_errors
def forget() -> None:
    cwd = _cwd()
    application.forget_project(cwd)
    console.ok(f"Project '{cwd.name}' is not welcome anymore.")
```

**Key change from old `cli.py`**: `detect` and `manage` now use `dataclasses.asdict()`
for serialization instead of `.model_dump()`, because `TechStack` is now a frozen
dataclass. `ManageProjectView` (Pydantic) handles the final serialization for `manage`.

### Package `__init__.py`

```python
from .ui.cli import project_app
from .infrastructure import Project

__all__ = ["project_app", "Project"]
```

---

## 9. Existing Test Updates (`tests/test_project_feature.py`)

| Existing test | Required change |
|---|---|
| `test_project_package_and_application_are_importable` | Update import path to `project_clean`; also import `project_clean.application` |
| `test_project_help_lists_expected_commands` | No change (CLI commands unchanged) |
| `test_manage_command_calls_application_and_renders_result` | Change `ManageProjectResult` → `ManageResult` from `project_clean.domain.entities`; update `captured[0]["block_configs"]` (key rename from `blocks_configs`) |

**New tests to add:**

1. `test_detect_stack_command_calls_application_and_renders` — monkeypatches
   `application.detect_stack`, asserts `console.print_dict` called with the right dict.
2. `test_manifest_repository_contract` — unit tests `YamlManifestStore` against a
   `tmp_path` fixture (exists, save, load, delete, resources_folder).
3. `test_tech_stack_detector_returns_none_for_unknown` — calls `TechFacadeDetector`
   with an empty temp dir; asserts `None`.
4. `test_manage_project_command_result` — integration-style: given a monkeypatched
   `BlockSystemGateway` and `TechFacadeDetector`, calls `commands.manage_project()`,
   asserts `ManageResult` fields.

---

## 10. Rollout Sequence

Build `project_clean/` in-place, then swap it into the main CLI.

```
Step 1  Create project_clean/{domain,application,infrastructure,ui}/__init__.py stubs
Step 2  Implement domain/entities.py and domain/repository.py
Step 3  Implement infrastructure/{manifest_store,tech_stack,block_gateway}.py
Step 4  Implement infrastructure/interface.py and infrastructure/__init__.py
Step 5  Implement application/{commands,queries}.py and application/__init__.py
Step 6  Implement ui/{views,cli}.py and project_clean/__init__.py
Step 7  Update tests/test_project_feature.py and add new unit tests
Step 8  Run: uv run pytest tests/test_project_feature.py -v
Step 9  Update freeloader/cli.py: swap import from project to project_clean
Step 10 Run: uv run pytest && uv run ruff check src/freeloader/project_clean/
Step 11 Rename src/freeloader/project/ → src/freeloader/project_old/
Step 12 Rename src/freeloader/project_clean/ → src/freeloader/project/
Step 13 Update all remaining import paths from project_old → project
Step 14 Delete src/freeloader/project_old/
Step 15 Final validation: uv run pytest && uv run ruff check
```

---

## 11. Validation Checklist

Before marking the migration complete, confirm all of the following:

- [ ] `uv run pytest tests/test_project_feature.py` passes with zero failures
- [ ] `uv run pytest` (full suite) passes with zero regressions
- [ ] `uv run ruff check src/freeloader/project/` reports no issues
- [ ] `fl project --help` shows detect, manage, provision, forget
- [ ] `fl project detect` works on the repo root
- [ ] `from freeloader.project import Project` works (machine API importable)
- [ ] No import of `freeloader.project.models`, `freeloader.project.application`,
      `freeloader.project.usecases`, or `freeloader.project.adapters` remains
      outside the `project/` package itself
- [ ] `project/domain/` has no imports from `application/`, `infrastructure/`, or `ui/`
- [ ] `project/application/` has no imports from `infrastructure/` classes directly
      (only from the factory functions in `infrastructure/__init__.py`)

---

## 12. Risk Notes

| Risk | Mitigation |
|---|---|
| `TechStack` changes from Pydantic to dataclass — callers using `.model_dump()` break | Audit all call sites before Step 9; the only external caller is `cli.py` (already updated in plan) |
| `ManageResult.block_configs` key differs from old `ManageProjectResult.blocks_configs` | Update test assertions at Step 7; check for any other callers |
| `BlockRef` is a Pydantic model from `freeloader.block` — `dataclasses.asdict()` may not traverse it | Use `block_gateway.get_manifest_configs()` to return plain dicts; `BlockRef` remains in `Manifest.block_refs` only for provision/forget, passed as-is to `BlockSystemGateway` |
| `TechFacadeDetector` uses `**detected` to construct `TechStack` — dict may have extra keys | Add an explicit field filter or use `TechStack(**{k: v for k, v in detected.items() if k in TechStack.__dataclass_fields__})` |
