# Step 3 — Application Layer

Build the use-case and public facade layer. Application code may import from
`freeloader.block_clean.domain` and call `infrastructure.__init__` factory functions.
**Commands and queries must remain thin** — they obtain repositories, wire services,
delegate, and return. Any non-trivial orchestration (multi-step loops, context
accumulation, cross-cutting concerns) belongs in a service class inside
`application/services/`.

Infrastructure implementation classes (`FileSystemBlockLoader`, `SourceBlock`,
`SecretsAdapter`) must never be imported by application code. The permitted
exceptions are documented per file below.

**Prerequisite:** Steps 1 and 2 are complete and ruff-clean.

Reference: `docs/FEATURE_ARCHITECTURE.md` §Application.

---

## Files to Create

```
src/freeloader/block_clean/application/
├── __init__.py
├── interface.py
├── commands.py
├── queries.py
└── services/
    ├── __init__.py
    └── provisioner/
        ├── __init__.py
        ├── models.py
        └── service.py
```

---

## Design principle: thin commands and queries, services for orchestration

**Direction of calls:** `interface` → `commands` → `services`. Services never call
commands.

**Commands** wire and invoke. A command function accepts only primitives, `Path`,
and plain domain DTOs — never repository ABCs, infrastructure objects, or service
classes. Internally it:
1. Obtains a `BlockRepository` via `load_block_repository()`.
2. Obtains a `SecretsReader` via `load_secrets_reader()` when needed.
3. Constructs any infrastructure adapters it needs (e.g. `BlockRunner`).
4. Constructs the appropriate service.
5. Calls one method on the service and returns its result.

**Queries** also keep primitive-only signatures. They obtain repositories and any
other needed adapters via infrastructure factory functions, then return domain
entities or plain Python types.

**Services** own all non-trivial logic. Result types (dataclasses) live inside the
service package alongside the service class — not in `commands.py`.

**Services are packages**, not single files, when they own both models and behaviour.
The `provisioner` service package owns: `models.py` (result types) and `service.py`
(orchestration class + private helpers).

Application-service modules may depend on feature-local infrastructure collaborators
that were already wired by commands. They must not perform environment lookup or
factory wiring themselves.

---

## Task 3.1 — `application/queries.py`

Query functions are read-only operations. They obtain a `BlockRepository` from the
infrastructure factory and return domain entities or plain Python types. No mutation,
no Terraform execution.

Allowed infrastructure imports: `load_block_repository` and `load_secrets_reader`
from `..infrastructure` only. No concrete implementation classes. Use relative
imports within `block_clean`.

### `get_manifest_configs`

Port logic from `block/orchestrator.py::ConfigOrchestrator.build_manifest_configs`.
Convert from a class method to a standalone function.

`BlockContract.collect_defaults()` was removed (Step 1) — the policy of which
config groups to include belongs here. `BlockContract` does not carry a
`tech_stack_field_names` computed property; compute the list inline using the
module-level `_TECH_STACK_KEYS` constant. The `required_tech_stack` flag lives on
`BlockMeta` and is accessed as `contract.block.required_tech_stack`.

```python
from freeloader.shared.types import ConfigValue

from ..infrastructure import load_block_repository, load_secrets_reader


_TECH_STACK_KEYS = frozenset(
    {"language", "language_version", "package_manager", "framework"}
)


def get_manifest_configs(
    tech_stack: dict[str, str],
    full_config: bool,
    project_name: str | None = None,
) -> dict[str, dict[str, ConfigValue]]:
    repository = load_block_repository()
    secrets = load_secrets_reader()
    blocks = repository.load_all()
    configs: dict[str, dict[str, ConfigValue]] = {}

    for block_id, block in blocks.items():
        contract = block.contract

        required_secrets = contract.required_secret_keys
        if required_secrets and not secrets.has_secrets(required_secrets):
            continue

        groups = ["basic", "advanced"] if full_config else ["basic"]
        # collect_defaults was removed from BlockContract (application concern);
        # inline the policy here, including project-name-derived defaults.
        config: dict[str, ConfigValue] = {}
        for field in contract.config:
            if field.group not in groups:
                continue
            if field.project_name_default and project_name is not None:
                config[field.name] = project_name
            elif field.default is not None:
                config[field.name] = field.default

        if contract.block.required_tech_stack and tech_stack:
            tech_stack_field_names = [
                f.name for f in contract.config if f.name in _TECH_STACK_KEYS
            ]
            config = _apply_tech_stack(config, tech_stack_field_names, tech_stack)

        configs[block_id] = config

    return configs


def _apply_tech_stack(
    config: dict[str, ConfigValue],
    field_names: list[str],
    tech_stack: dict[str, str],
) -> dict[str, ConfigValue]:
    for field_name in field_names:
        value = tech_stack.get(field_name)
        if value is not None:
            config[field_name] = value
    return config
```

Source: `block/orchestrator.py`.

---

## Task 3.2 — `application/services/provisioner/models.py`

All result dataclasses for the provisioning service live here — not in `commands.py`.
They move from `block/provision/models.py`, with the key change that
`ProvisioningStep.block` now holds a domain `Block`. No infrastructure imports.

```python
from __future__ import annotations

from dataclasses import dataclass

from freeloader.shared.types import ConfigValue

from ....domain.entity import Block, ResolvedBlock


@dataclass(frozen=True)
class ProvisioningStep:
    block: Block
    resolved_block: ResolvedBlock

    @property
    def id(self) -> str:
        return self.resolved_block.id

    @property
    def has_inputs(self) -> bool:
        return bool(self.resolved_block.inputs)


@dataclass(frozen=True)
class ProvisioningPlan:
    steps: list[ProvisioningStep]

    @property
    def block_ids(self) -> list[str]:
        return [step.id for step in self.steps]


@dataclass(frozen=True)
class AppliedStepReport:
    block_id: str
    outputs: dict[str, ConfigValue | None]
    had_dependency_inputs: bool


@dataclass(frozen=True)
class ProvisioningReport:
    plan: ProvisioningPlan
    applied_steps: list[AppliedStepReport]

    @property
    def outputs_by_block(self) -> dict[str, dict[str, ConfigValue | None]]:
        return {step.block_id: dict(step.outputs) for step in self.applied_steps}


@dataclass(frozen=True)
class DestroyStepReport:
    block_id: str
    destroyed: bool
    error: str = ""


@dataclass(frozen=True)
class DestroyReport:
    plan: ProvisioningPlan
    steps: list[DestroyStepReport]

    @property
    def destroyed_block_ids(self) -> list[str]:
        return [step.block_id for step in self.steps if step.destroyed]

    @property
    def failed_block_ids(self) -> list[str]:
        return [step.block_id for step in self.steps if not step.destroyed]
```

---

## Task 3.3 — `application/services/provisioner/service.py`

`BlockProvisioningService` owns all provisioning and destroy orchestration.
Port `Provisioner.provision` and `Provisioner.destroy` from `block/provisioner.py`,
and `Provisioner.plan` as `build_plan`.

Permitted infrastructure imports (service is the orchestration boundary):
`BlockRunner` (calls), `ProvisioningResource` (construction). Use relative imports
within `block_clean`.

`_ExecutionContext` is a private helper class. It tracks block outputs during the
provisioning loop and computes tfvar names from `OutputReference.requirement_key`.
The tfvar rename (`replace(".", "_")`) keeps the Terraform naming convention out of
the domain — `OutputReference` carries the pre-decomposed `output_name` and
`provider_id`; the service adds the tfvar step.

`BlockRunner.run_init` has a single signature with an optional `extra_vars` parameter
(Steps 1 and 2 collapsed the old `run_init` / `run_init_with_deps` pair). The
two-phase init pattern (first without deps in `_prepare_resources`, then again with
resolved deps inside the loop) is preserved via the optional argument.

```python
from __future__ import annotations

from pathlib import Path

from freeloader.shared.types import ConfigValue

from ....domain.entity import BlockRef, OutputReference
from ....domain.repository import BlockRepository
from ....domain.resolver import DAGResolver
from ....domain.value_object import BlockId
from ....infrastructure.resource import ProvisioningResource
from ....infrastructure.runner import BlockRunner

from .models import (
    AppliedStepReport,
    DestroyReport,
    DestroyStepReport,
    ProvisioningPlan,
    ProvisioningReport,
    ProvisioningStep,
)


class _ExecutionContext:
    """Accumulates block outputs during the provisioning loop."""

    def __init__(self) -> None:
        self._outputs: dict[str, dict[str, ConfigValue | None]] = {}

    def set_outputs(self, block_id: str, outputs: dict[str, ConfigValue | None]) -> None:
        self._outputs[block_id] = outputs

    def resolve_inputs(
        self, inputs: list[OutputReference]
    ) -> dict[str, ConfigValue | None]:
        """Return {tfvar_name: value} pairs for a block's declared inputs."""
        result: dict[str, ConfigValue | None] = {}
        for ref in inputs:
            tfvar_name = ref.requirement_key.replace(".", "_")
            result[tfvar_name] = self._outputs.get(ref.provider_id, {}).get(ref.output_name)
        return result


class BlockProvisioningService:
    """Orchestrates block provisioning and destroy flows."""

    def __init__(self, repository: BlockRepository, runner: BlockRunner) -> None:
        self._repository = repository
        self._runner = runner

    def build_plan(self, block_refs: list[BlockRef]) -> ProvisioningPlan:
        assert block_refs, "At least one block reference must be provided"
        block_ids = [BlockId(ref.resolved_id) for ref in block_refs]
        blocks = self._repository.load_by_ids(block_ids)
        contracts = {bid: block.contract for bid, block in blocks.items()}
        resolved_blocks = DAGResolver().resolve(block_refs, contracts)
        return ProvisioningPlan(
            steps=[
                ProvisioningStep(block=blocks[rb.id], resolved_block=rb)
                for rb in resolved_blocks
            ]
        )

    def provision(
        self, resources_root: Path, block_refs: list[BlockRef]
    ) -> ProvisioningReport:
        plan = self.build_plan(block_refs)
        context = _ExecutionContext()
        resources = self._prepare_resources(plan, resources_root)
        applied_steps: list[AppliedStepReport] = []

        for step in plan.steps:
            resource = resources[step.id]
            if step.has_inputs:
                extra_vars = context.resolve_inputs(step.resolved_block.inputs)
                self._runner.run_init(resource, step.resolved_block, extra_vars)
                self._runner.run_plan(resource)

            output = self._runner.run_apply(resource)
            context.set_outputs(step.id, output)
            applied_steps.append(
                AppliedStepReport(
                    block_id=step.id,
                    outputs=output,
                    had_dependency_inputs=step.has_inputs,
                )
            )

        return ProvisioningReport(plan=plan, applied_steps=applied_steps)

    def destroy(
        self, resources_root: Path, block_refs: list[BlockRef]
    ) -> DestroyReport:
        plan = self.build_plan(block_refs)
        steps: list[DestroyStepReport] = []

        for step in reversed(plan.steps):
            resource: ProvisioningResource | None = None
            try:
                resource_folder = resources_root / step.id
                resource = ProvisioningResource(resource_folder)
                self._runner.run_destroy(resource)
                steps.append(DestroyStepReport(block_id=step.id, destroyed=True))
            except Exception as e:
                steps.append(
                    DestroyStepReport(block_id=step.id, destroyed=False, error=str(e))
                )
            finally:
                if resource is not None:
                    resource.rm()

        return DestroyReport(plan=plan, steps=steps)

    def _prepare_resources(
        self,
        plan: ProvisioningPlan,
        resources_root: Path,
    ) -> dict[str, ProvisioningResource]:
        """Initialize Terraform workspaces for all planned steps (first pass, no deps)."""
        resources: dict[str, ProvisioningResource] = {}
        for step in plan.steps:
            resource_folder = resources_root / step.id
            resource = ProvisioningResource(resource_folder)
            self._repository.dump_assets(step.block.id, resource.folder)
            self._runner.run_init(resource, step.resolved_block)
            resources[step.id] = resource
        return resources
```

Source: `block/provisioner.py`.

---

## Task 3.4 — `application/services/provisioner/__init__.py`

Re-export the full public surface of the provisioner package.

```python
from .models import (
    AppliedStepReport,
    DestroyReport,
    DestroyStepReport,
    ProvisioningPlan,
    ProvisioningReport,
    ProvisioningStep,
)
from .service import BlockProvisioningService

__all__ = [
    "AppliedStepReport",
    "BlockProvisioningService",
    "DestroyReport",
    "DestroyStepReport",
    "ProvisioningPlan",
    "ProvisioningReport",
    "ProvisioningStep",
]
```

---

## Task 3.5 — `application/services/__init__.py`

Re-export the public surface of the services sub-package.

```python
from .provisioner import BlockProvisioningService

__all__ = ["BlockProvisioningService"]
```

---

## Task 3.6 — `application/commands.py`

Thin command functions. Each command accepts only primitives, `Path`, and plain
domain DTOs — never repository ABCs, infrastructure objects, or service classes.
Internally it loads repositories/adapters, constructs the runner, wires the service,
and delegates. No orchestration lives here. Result types are imported from
`services.provisioner` — `commands.py` defines no dataclasses of its own.

Allowed infrastructure imports: `load_block_repository` and `load_secrets_reader`
from `..infrastructure`, plus `BlockRunner` from `..infrastructure.runner`
(constructed internally, not in the signature).

```python
from pathlib import Path

from ..domain.entity import BlockRef
from ..infrastructure import load_block_repository, load_secrets_reader
from ..infrastructure.runner import BlockRunner

from .services.provisioner import BlockProvisioningService, DestroyReport, ProvisioningReport


def provision_blocks(
    project_root: Path,
    resources_root: Path,
    block_refs: list[BlockRef],
) -> ProvisioningReport:
    repository = load_block_repository()
    runner = BlockRunner(project_root, load_secrets_reader())
    service = BlockProvisioningService(repository, runner)
    return service.provision(resources_root, block_refs)


def destroy_blocks(
    project_root: Path,
    resources_root: Path,
    block_refs: list[BlockRef],
) -> DestroyReport:
    repository = load_block_repository()
    runner = BlockRunner(project_root, load_secrets_reader())
    service = BlockProvisioningService(repository, runner)
    return service.destroy(resources_root, block_refs)
```

---

## Task 3.7 — `application/interface.py`

The `Blocks` class is the public facade consumed by other features (currently `project`).
It replaces both `block/facade.py::BlocksFacade` and the free functions in
`block/ports/interface.py`.

The facade holds only `project_root` — no secrets object, no runner, no service,
no repository. It passes primitives and domain DTOs to commands/queries, matching
their signatures exactly.

```python
from pathlib import Path

from freeloader.shared.types import ConfigValue

from ..domain.entity import BlockRef

from . import commands, queries
from .services.provisioner import DestroyReport, ProvisioningReport


class Blocks:
    def __init__(self, project_root: Path) -> None:
        self._project_root = project_root

    @classmethod
    def for_project(cls, project_root: Path) -> "Blocks":
        """Construct a Blocks facade scoped to one project root."""
        return cls(project_root=project_root)

    def manifest_configs(
        self,
        tech_stack: dict[str, str],
        full_config: bool,
        project_name: str | None = None,
    ) -> dict[str, dict[str, ConfigValue]]:
        return queries.get_manifest_configs(
            tech_stack=tech_stack,
            full_config=full_config,
            project_name=project_name,
        )

    def provision(
        self,
        resources_root: Path,
        block_refs: list[BlockRef],
    ) -> ProvisioningReport:
        return commands.provision_blocks(
            project_root=self._project_root,
            resources_root=resources_root,
            block_refs=block_refs,
        )

    def destroy(
        self,
        resources_root: Path,
        block_refs: list[BlockRef],
    ) -> DestroyReport:
        return commands.destroy_blocks(
            project_root=self._project_root,
            resources_root=resources_root,
            block_refs=block_refs,
        )
```

Design notes:
- `for_project` is the primary constructor for callers.
- The facade holds no secrets reader, runner, service, or repository — commands and
    queries wire infrastructure internally.
- Result types are imported from `services.provisioner`, not from `commands`,
  because they live in the service package.
- The facade calls `commands` and `queries` as modules so tests can monkeypatch
  `interface.commands.provision_blocks`.

---

## Task 3.8 — `application/__init__.py`

Re-export the public surface of the application layer. Result types come from
`services.provisioner`, reflecting where they actually live.

```python
from .interface import Blocks
from .services.provisioner import (
    AppliedStepReport,
    DestroyReport,
    DestroyStepReport,
    ProvisioningPlan,
    ProvisioningReport,
    ProvisioningStep,
)

__all__ = [
    "Blocks",
    "AppliedStepReport",
    "DestroyReport",
    "DestroyStepReport",
    "ProvisioningPlan",
    "ProvisioningReport",
    "ProvisioningStep",
]
```

(No changes from before — all imports here are already relative within `application/`.)

---

## Verification

After completing all tasks in this step, confirm:

1. `uv run ruff check src/freeloader/block_clean/application/` reports no errors.
2. Import rules by file:
    - `queries.py` — only `..infrastructure.load_block_repository` and `..infrastructure.load_secrets_reader`; no implementation classes.
    - `commands.py` — `..infrastructure.load_block_repository`, `..infrastructure.load_secrets_reader`, and `..infrastructure.runner.BlockRunner` (constructed internally); no infra objects in signatures; no dataclasses defined here.
   - `services/provisioner/models.py` — no infrastructure or application imports; domain types via `....domain`.
    - `services/provisioner/service.py` — may import `BlockRunner` and `ProvisioningResource` via `....infrastructure`; must not import `FileSystemBlockLoader`, `SourceBlock`, or `SecretsAdapter`.
    - `interface.py` — no infrastructure imports; no runner, no service, no repository on `self`.
3. Command signatures accept only `Path` and `list[BlockRef]`. Query signatures accept only plain Python types (`dict[str, str]`, `bool`, `str | None`). No infra, repository, or service objects appear in any public application signature.
4. Call direction: `interface` → `commands` → `services`. No backwards imports.
5. All imports within `block_clean` are relative (`..domain`, `..infrastructure`, `....domain`, etc.). `freeloader.shared` stays absolute.
6. No application file imports from `freeloader.block` (old package).
7. `from freeloader.block_clean.application import Blocks` works.
8. `from freeloader.block_clean.application import ProvisioningReport, DestroyReport` works.
9. Constructing `Blocks.for_project(Path("."))` does not raise (environment and secrets lookup are deferred to actual method calls).
