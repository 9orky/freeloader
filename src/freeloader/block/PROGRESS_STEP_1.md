# Progress Step 1: Block Feature Implementation

## Scope

This step introduces progress streaming at the source of truth: the block feature.
Nothing in this step should render UI or print to the terminal. The only job here is
to emit a stable, ordered stream of domain events that precisely matches real block
provisioning and destroy execution.

## Outcome

After this step, the block feature exposes two new streaming APIs:

- `provision_events(...) -> Iterator[BlockProvisionEvent]`
- `destroy_events(...) -> Iterator[BlockDestroyEvent]`

The existing synchronous APIs still work:

- `provision(...) -> ProvisioningReport`
- `destroy(...) -> DestroyReport`

Those synchronous methods become wrappers that drain the generator and return the
terminal report from the final event.

## Files To Add

- `src/freeloader/block/domain/events.py`
- `src/freeloader/block/domain/provisioning.py`

## Files To Change

- `src/freeloader/block/domain/__init__.py`
- `src/freeloader/block/application/services/provisioner/service.py`
- `src/freeloader/block/application/services/provisioner/__init__.py`
- `src/freeloader/block/application/commands.py`
- `src/freeloader/block/application/interface.py`
- `src/freeloader/block/application/__init__.py`
- `src/freeloader/block/__init__.py`
- `tests/test_block_provisioner.py`

## 1. Domain Event Model

Create `domain/events.py` with frozen dataclasses only. Keep them simple and explicit.
Do not inherit from a generic event base class unless a clear need appears during
implementation.

Recommended types:

```python
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias

from freeloader.shared.types import ConfigValue

from .provisioning import DestroyReport, ProvisioningReport


ProvisionPhase = Literal["prepare", "dependency_inputs", "apply"]


@dataclass(frozen=True)
class ProvisioningStarted:
    total_blocks: int
    block_ids: list[str]


@dataclass(frozen=True)
class BlockPreparationStarted:
    block_id: str
    index: int
    total: int


@dataclass(frozen=True)
class BlockPreparationCompleted:
    block_id: str
    index: int
    total: int


@dataclass(frozen=True)
class BlockApplyStarted:
    block_id: str
    index: int
    total: int
    has_dependency_inputs: bool


@dataclass(frozen=True)
class BlockDependencyInputsStarted:
    block_id: str
    index: int
    total: int
    provider_ids: list[str]


@dataclass(frozen=True)
class BlockApplyCompleted:
    block_id: str
    index: int
    total: int
    outputs: dict[str, ConfigValue | None]


@dataclass(frozen=True)
class ProvisioningFailed:
    block_id: str
    phase: ProvisionPhase
    error: str


@dataclass(frozen=True)
class ProvisioningFinished:
    report: ProvisioningReport


@dataclass(frozen=True)
class DestroyStarted:
    total_blocks: int
    block_ids: list[str]


@dataclass(frozen=True)
class BlockDestroyStarted:
    block_id: str
    index: int
    total: int


@dataclass(frozen=True)
class BlockDestroyCompleted:
    block_id: str
    index: int
    total: int


@dataclass(frozen=True)
class BlockDestroyFailed:
    block_id: str
    index: int
    total: int
    error: str


@dataclass(frozen=True)
class DestroyFinished:
    report: DestroyReport


BlockProvisionEvent: TypeAlias = (
    ProvisioningStarted
    | BlockPreparationStarted
    | BlockPreparationCompleted
    | BlockApplyStarted
    | BlockDependencyInputsStarted
    | BlockApplyCompleted
    | ProvisioningFailed
    | ProvisioningFinished
)


BlockDestroyEvent: TypeAlias = (
    DestroyStarted
    | BlockDestroyStarted
    | BlockDestroyCompleted
    | BlockDestroyFailed
    | DestroyFinished
)
```

Implementation note:

- do not import report models from `application/` into `domain/events.py`
- move `ProvisioningStep`, `ProvisioningPlan`, `AppliedStepReport`, `ProvisioningReport`,
    `DestroyStepReport`, and `DestroyReport` into `domain/provisioning.py`, then import
    them from there in both `events.py` and the provisioning service

## 2. Service API Changes

Add two generator methods on `BlockProvisioningService`:

- `provision_events(self, resources_root: Path, block_refs: list[BlockRef]) -> Iterator[BlockProvisionEvent]`
- `destroy_events(self, resources_root: Path, block_refs: list[BlockRef]) -> Iterator[BlockDestroyEvent]`

Keep the existing methods:

- `provision(...)`
- `destroy(...)`

Their new implementation pattern should be:

```python
def provision(...) -> ProvisioningReport:
    report: ProvisioningReport | None = None
    for event in self.provision_events(resources_root, block_refs):
        if isinstance(event, ProvisioningFinished):
            report = event.report
    assert report is not None
    return report
```

Apply the same pattern for destroy.

## 3. Event Emission Rules

The generator must emit events in the same order that the work actually happens.
That order is more important than elegance.

### Provision order

1. Build the plan.
2. Emit `ProvisioningStarted(total_blocks, block_ids)`.
3. For each step during initial preparation:
   - emit `BlockPreparationStarted`
   - dump assets
   - run init
   - run plan
   - emit `BlockPreparationCompleted`
4. For each step during apply:
   - emit `BlockApplyStarted`
   - if dependency inputs exist:
     - compute `provider_ids`
         - emit `BlockDependencyInputsStarted`
     - run init with extra vars
     - run plan again
   - run apply
   - capture outputs
   - emit `BlockApplyCompleted`
5. Build the final `ProvisioningReport`.
6. Emit `ProvisioningFinished(report)`.

### Destroy order

1. Build the plan.
2. Emit `DestroyStarted(total_blocks, block_ids)`.
3. Iterate over steps in reverse order.
4. For each step:
   - emit `BlockDestroyStarted`
   - run destroy
   - if successful emit `BlockDestroyCompleted`
   - if failed emit `BlockDestroyFailed`
5. Build final `DestroyReport`.
6. Emit `DestroyFinished(report)`.

## 4. Failure Handling Contract

Provisioning failure behavior must be predictable.

Rules:

- preparation error -> emit `ProvisioningFailed(block_id, "prepare", error)` then re-raise
- dependency-input binding error -> emit `ProvisioningFailed(block_id, "dependency_inputs", error)` then re-raise
- apply error -> emit `ProvisioningFailed(block_id, "apply", error)` then re-raise

Destroy failure differs slightly because current destroy already accumulates per-block
failures into the report instead of aborting the whole loop. Keep that existing policy.

Rules for destroy:

- emit `BlockDestroyFailed` for a failed block
- continue destroying remaining blocks
- still emit `DestroyFinished(report)` at the end

## 5. Service Refactor Details

Refactor the current service in a way that keeps execution readable.

Recommended internal split inside `service.py`:

- `_prepare_resources_events(...) -> Iterator[BlockProvisionEvent]`
- `_apply_step_events(...) -> Iterator[BlockProvisionEvent]`
- `_destroy_step_events(...) -> Iterator[BlockDestroyEvent]`

Keep `_ExecutionContext` as the holder for dependency outputs. It already captures the
right state.

Do not try to turn the whole service into tiny abstractions. The useful unit here is a
generator per phase, not a class hierarchy.

## 6. Application Boundary Changes

Add streaming functions in `block/application/commands.py`:

- `provision_blocks_events(...)`
- `destroy_blocks_events(...)`

They should wire repository and runner exactly the same way as the current commands,
then return the underlying service generator.

Add matching facade methods in `block/application/interface.py`:

- `Blocks.provision_events(...)`
- `Blocks.destroy_events(...)`

These methods should not do any formatting, aggregation, or buffering. They are just
machine API pass-through methods.

## 7. Package Exports

Re-export the new event types from the block package root so other features can depend
on them without importing deep internal modules.

Recommended exports:

- `Blocks`
- `BlockRef`
- `BlockProvisionEvent`
- `BlockDestroyEvent`
- all concrete event dataclasses that project UI needs for `isinstance` checks

## 8. Test Plan For Step 1

Extend `tests/test_block_provisioner.py`.

Add these tests:

### Event order on successful provision

For a two-block dependency graph, assert this exact high-level order:

1. `ProvisioningStarted`
2. `BlockPreparationStarted(git.repo)`
3. `BlockPreparationCompleted(git.repo)`
4. `BlockPreparationStarted(docker.image)`
5. `BlockPreparationCompleted(docker.image)`
6. `BlockApplyStarted(git.repo)`
7. `BlockApplyCompleted(git.repo)`
8. `BlockApplyStarted(docker.image)`
9. `BlockDependencyInputsStarted(docker.image)`
10. `BlockApplyCompleted(docker.image)`
11. `ProvisioningFinished`

### Failure event before re-raise

Make the fake runner fail in one phase and assert:

- the matching `ProvisioningFailed` event is yielded
- the original call still raises

### Wrapper compatibility

Assert that `service.provision(...)` still returns the same `ProvisioningReport` shape
as before.

## 9. Done Criteria For Step 1

This step is done when:

- block service emits ordered progress events for provision and destroy
- synchronous APIs still return the existing report types
- failure events are emitted with correct phase names
- event types are publicly importable from the block package root
- block-side tests cover success order and failure behavior