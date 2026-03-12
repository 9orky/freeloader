# Step 3 — Application Layer

Build the use-case and public facade layer. Application code may import from
`freeloader.block_clean.domain` and call `infrastructure.__init__` factory functions,
but **must not instantiate or import infrastructure implementation classes directly**
(e.g., `FileSystemBlockLoader`, `BlockRunner`). It never performs I/O itself.

**Prerequisite:** Steps 1 and 2 are complete and ruff-clean.

Reference: `docs/FEATURE_ARCHITECTURE.md` §Application.

---

## Files to Create

```
src/freeloader/block_clean/application/
├── __init__.py
├── interface.py
├── commands.py
└── queries.py
```

---

## Task 3.1 — `application/queries.py`

Query functions are read-only operations. They obtain a `BlockRepository` from the
infrastructure factory and return domain entities or plain Python types. No mutation,
no Terraform execution.

### `get_manifest_configs`

Port logic from `block/orchestrator.py::ConfigOrchestrator.build_manifest_configs`.
Convert from a class method to a standalone function.

```python
from freeloader.shared.types import ConfigValue

from freeloader.block_clean.domain.entity import Block
from freeloader.block_clean.domain.repository import SecretsReader
from freeloader.block_clean.infrastructure import load_block_repository


def get_manifest_configs(
    secrets: SecretsReader,
    tech_stack: dict[str, str],
    full_config: bool,
    project_name: str | None = None,
) -> dict[str, dict[str, ConfigValue]]:
    repository = load_block_repository()
    blocks = repository.load_all()
    configs: dict[str, dict[str, ConfigValue]] = {}

    for block_id, block in blocks.items():
        contract = block.contract

        required_secrets = contract.required_secret_keys
        if required_secrets and not secrets.has_secrets(required_secrets):
            continue

        groups = ["basic", "advanced"] if full_config else ["basic"]
        # collect_defaults was removed from BlockContract (application concern);
        # inline the logic here.
        config: dict[str, ConfigValue] = {
            f.name: f.default
            for f in contract.config
            if f.group in groups and f.default is not None
        }

        if contract.block.required_tech_stack and tech_stack:
            _TECH_STACK_KEYS = frozenset(
                {"language", "language_version", "package_manager", "framework"}
            )
            tech_stack_field_names = [f.name for f in contract.config if f.name in _TECH_STACK_KEYS]
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

Note: `dump_config()` was a method on the old `Block` infra class. Here we replicate
its logic inline using only the domain `BlockContract` — this removes the infra
dependency from query logic.

Source: `block/orchestrator.py`.

---

## Task 3.2 — `application/commands.py`

This file has two responsibilities: (1) define the result dataclasses for provisioning
and destroy operations, and (2) implement the `provision_blocks` and `destroy_blocks`
command functions.

### 3.2a — Result dataclasses

These are pure value types. They move here from `block/provision/models.py`, and the
critical change is that `ProvisioningStep.block` now holds a domain `Block` (not the
old infra `Block`). No infrastructure imports allowed here.

```python
from __future__ import annotations

from dataclasses import dataclass

from freeloader.shared.types import ConfigValue

from freeloader.block_clean.domain.entity import Block, BlockRef, ResolvedBlock


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

### 3.2b — `_plan` helper and `_ExecutionContext` (internal)

Port `Provisioner.plan` from `block/provisioner.py` as a module-private function.
`ExecutionContext` is defined here (application layer) as a private class that tracks
block outputs during the provisioning loop. It is **not** part of the domain.

`_resolve_inputs` is a helper that converts the domain `inputs` (a `list[OutputReference]`)
into a `{tfvar_name: value}` dict by looking up outputs from the context. The tfvar name
computation (`req_key.replace(".", "_")`) lives here, keeping the Terraform naming
convention out of the domain. `OutputReference` carries the pre-decomposed `output_name`
and `provider_id` — the application only adds the tfvar renaming step.

```python
from pathlib import Path

from freeloader.block_clean.domain.entity import BlockRef, OutputReference
from freeloader.block_clean.domain.repository import BlockRepository
from freeloader.block_clean.domain.resolver import DAGResolver
from freeloader.block_clean.domain.value_object import BlockId
from freeloader.block_clean.infrastructure import load_block_repository
from freeloader.block_clean.infrastructure.runner import BlockRunner
from freeloader.block_clean.infrastructure.resource import ProvisioningResource


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


def _plan(repository: BlockRepository, block_refs: list[BlockRef]) -> ProvisioningPlan:
    assert block_refs, "At least one block reference must be provided"
    block_ids = [BlockId(ref.resolved_id) for ref in block_refs]
    blocks = repository.load_by_ids(block_ids)
    contracts = {bid: block.contract for bid, block in blocks.items()}
    resolved_blocks = DAGResolver().resolve(block_refs, contracts)

    return ProvisioningPlan(
        steps=[
            ProvisioningStep(block=blocks[rb.id], resolved_block=rb)
            for rb in resolved_blocks
        ]
    )
```

### 3.2c — `provision_blocks` command

Port `Provisioner.provision` from `block/provisioner.py` as a standalone function.
Infrastructure objects (`BlockRunner`, `ProvisioningResource`) are constructed inside
this function — they do not leak to the caller.

```python
def provision_blocks(
    resources_root: Path,
    block_refs: list[BlockRef],
    runner: BlockRunner,
) -> ProvisioningReport:
    repository = load_block_repository()
    plan = _plan(repository, block_refs)
    context = _ExecutionContext()
    resources = _prepare_resources(plan, repository, resources_root, runner)
    applied_steps: list[AppliedStepReport] = []

    for step in plan.steps:
        resource = resources[step.id]
        if step.has_inputs:
            extra_vars = context.resolve_inputs(step.resolved_block.inputs)
            runner.run_init(resource, step.resolved_block, extra_vars)
            runner.run_plan(resource)

        output = runner.run_apply(resource)
        context.set_outputs(step.id, output)
        applied_steps.append(
            AppliedStepReport(
                block_id=step.id,
                outputs=output,
                had_dependency_inputs=step.has_inputs,
            )
        )

    return ProvisioningReport(plan=plan, applied_steps=applied_steps)
```

Private helpers `_prepare_resources` and `_plan_resources`:

```python
def _prepare_resources(
    plan: ProvisioningPlan,
    repository: BlockRepository,
    resources_root: Path,
    runner: BlockRunner,
) -> dict[str, ProvisioningResource]:
    resources: dict[str, ProvisioningResource] = {}
    for step in plan.steps:
        resource_folder = resources_root / step.id
        resource = ProvisioningResource(resource_folder)
        repository.dump_assets(step.block.id, resource.folder)
        runner.run_init(resource, step.resolved_block)
        resources[step.id] = resource
    return resources
```

### 3.2d — `destroy_blocks` command

Port `Provisioner.destroy` from `block/provisioner.py`:

```python
def destroy_blocks(
    resources_root: Path,
    block_refs: list[BlockRef],
    runner: BlockRunner,
) -> DestroyReport:
    repository = load_block_repository()
    plan = _plan(repository, block_refs)
    steps: list[DestroyStepReport] = []

    for step in reversed(plan.steps):
        resource: ProvisioningResource | None = None
        try:
            resource_folder = resources_root / step.id
            resource = ProvisioningResource(resource_folder)
            runner.run_destroy(resource)
            steps.append(DestroyStepReport(block_id=step.id, destroyed=True))
        except Exception as e:
            steps.append(DestroyStepReport(block_id=step.id, destroyed=False, error=str(e)))
        finally:
            if resource is not None:
                resource.rm()

    return DestroyReport(plan=plan, steps=steps)
```

---

## Task 3.3 — `application/interface.py`

The `Blocks` class is the public facade consumed by other features (currently `project`).
It replaces both `block/facade.py::BlocksFacade` and the free functions in
`block/ports/interface.py`.

```python
import os
from pathlib import Path

from freeloader.shared.types import ConfigValue

from freeloader.block_clean.domain.entity import BlockRef
from freeloader.block_clean.domain.repository import SecretsReader
from freeloader.block_clean.infrastructure.runner import BlockRunner
from freeloader.block_clean.infrastructure.secrets import SecretsAdapter

from . import commands, queries
from .commands import DestroyReport, ProvisioningReport


class Blocks:
    def __init__(self, project_root: Path, secrets: SecretsReader) -> None:
        self._project_root = project_root
        self._secrets = secrets
        self._runner = BlockRunner(project_root, secrets)

    @classmethod
    def for_project(cls, project_root: Path) -> "Blocks":
        """Construct a Blocks facade wired to the default secrets namespace."""
        return cls(project_root=project_root, secrets=SecretsAdapter())

    def manifest_configs(
        self,
        tech_stack: dict[str, str],
        full_config: bool,
        project_name: str | None = None,
    ) -> dict[str, dict[str, ConfigValue]]:
        return queries.get_manifest_configs(
            secrets=self._secrets,
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
            resources_root=resources_root,
            block_refs=block_refs,
            runner=self._runner,
        )

    def destroy(
        self,
        resources_root: Path,
        block_refs: list[BlockRef],
    ) -> DestroyReport:
        return commands.destroy_blocks(
            resources_root=resources_root,
            block_refs=block_refs,
            runner=self._runner,
        )
```

Design notes:
- `for_project` is the primary constructor for callers. The `__init__` signature
  accepts an explicit `SecretsReader` to keep the class testable (inject a mock).
- `BlockRunner` is constructed here because it requires the project path and secrets,
  both of which are already held by the facade. This matches how `BlocksFacade`
  worked in the old code.
- The facade calls `commands` and `queries` as modules (not sub-paths) so tests can
  monkeypatch `blocks_facade.commands.provision_blocks`.

---

## Task 3.4 — `application/__init__.py`

Re-export the public surface of the application layer.

```python
from .interface import Blocks
from .commands import (
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

---

## Verification

After completing all tasks in this step, confirm:

1. `uv run ruff check src/freeloader/block_clean/application/` reports no errors.
2. No application file imports a concrete infrastructure class by name
   (`FileSystemBlockLoader`, `SourceBlock`, `BlockRunner`,`ProvisioningResource`,
   `SecretsAdapter`) — except `interface.py` which constructs `BlockRunner` and
   `SecretsAdapter` as a wiring point.
3. No application file imports from `freeloader.block` (old package).
4. `from freeloader.block_clean.application import Blocks` works.
5. `from freeloader.block_clean.application import ProvisioningReport, DestroyReport`
   works.
6. Constructing `Blocks.for_project(Path("."))` does not raise (the env var check
   is deferred to actual method calls).
