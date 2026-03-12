# Progress Step 2: Project Feature Implementation

## Scope

This step makes project provisioning consume and present the block event stream.
The project feature remains the presentation owner for user-facing progress, while the
block feature remains the execution owner.

This step should not move progress formatting into block.

## Outcome

After this step:

- `project` exposes streaming application functions for provision and forget
- the project block gateway forwards event iterators
- the project CLI renders live progress while blocks are running
- the current user-facing commands still finish with the existing success or error
  behavior

## Files To Add

- `src/freeloader/project/ui/progress.py`

## Files To Change

- `src/freeloader/project/domain/repository.py`
- `src/freeloader/project/infrastructure/block_gateway.py`
- `src/freeloader/project/application/commands.py`
- `src/freeloader/project/application/__init__.py`
- `src/freeloader/project/ui/cli.py`
- `tests/test_project_feature.py`

## 1. Extend The Project Gateway Contract

Add iterator-based methods to `project/domain/repository.py` on `BlockGateway`:

- `provision_events(...) -> Iterator[BlockProvisionEvent]`
- `destroy_events(...) -> Iterator[BlockDestroyEvent]`

Use imports from the block package root only. Do not import from
`freeloader.block.domain.events` directly in the project domain layer.

This keeps the project feature coupled only to the block feature's public API.

## 2. Forward Events In The Concrete Gateway

Update `project/infrastructure/block_gateway.py`:

- keep current `provision(...)` and `destroy(...)`
- add `provision_events(...)`
- add `destroy_events(...)`

Implementation rule:

- streaming gateway methods should return the iterator directly from
  `Blocks.for_project(project_root)`
- synchronous gateway methods should keep using the synchronous block facade methods

Do not consume the iterator in infrastructure. If the gateway drains the stream, the
CLI can no longer present real-time updates.

## 3. Add Project Application Streaming Functions

Add these functions in `project/application/commands.py`:

- `provision_project_events(folder: Path)`
- `forget_project_events(folder: Path)`

Both functions should:

1. load the manifest
2. resolve the resources folder
3. call the gateway streaming method
4. return the iterator unchanged

Keep existing synchronous functions:

- `provision_project(folder)`
- `forget_project(folder)`

Their new implementation should drain the streaming variant rather than duplicating
the logic.

Pattern:

```python
def provision_project(folder: Path) -> None:
    for _event in provision_project_events(folder):
        pass
```

This keeps the application layer as the single orchestration entry point.

## 4. Add Dedicated Project UI Progress Adapter

Create `src/freeloader/project/ui/progress.py`.

This file is important. Progress is fundamentally a CLI UI concern, and the CLI should
not accumulate a long chain of `isinstance` checks inline inside `ui/cli.py`.

Recommended responsibilities of `project/ui/progress.py`:

- map block events to user-facing status text
- define durable success and failure lines
- provide one high-level function that drives rendering while consuming the iterator

Recommended shape:

```python
from __future__ import annotations

from collections.abc import Iterable

from freeloader.block import (
    BlockApplyCompleted,
    BlockApplyStarted,
    BlockDependencyInputsStarted,
    BlockDestroyCompleted,
    BlockDestroyFailed,
    BlockDestroyStarted,
    BlockPreparationStarted,
    DestroyFinished,
    DestroyStarted,
    ProvisioningFailed,
    ProvisioningFinished,
    ProvisioningStarted,
)
from freeloader.shared.console.progress import run_status_stream


def render_project_provision_progress(events: Iterable[object]) -> None:
    ...


def render_project_forget_progress(events: Iterable[object]) -> None:
    ...
```

Keep this file project-specific. It can understand wording like `Preparing`,
`Applying`, `Destroying`, and project command semantics.

## 5. CLI Wiring

Update `project/ui/cli.py`.

### Provision command

Current behavior:

- call `application.provision_project(folder)`
- print final success line

New behavior:

1. call `application.provision_project_events(folder)`
2. pass the iterator to `render_project_provision_progress(...)`
3. after the renderer completes without error, print the existing final success line

### Forget command

Apply the same pattern using `forget_project_events(folder)` and
`render_project_forget_progress(...)`.

### Error handling

Do not swallow exceptions in the progress adapter. Let `@console.handle_errors` on the
CLI command keep the current exit behavior.

## 6. Event To Message Mapping

Keep the initial wording short and durable.

Recommended mapping for provision:

- `ProvisioningStarted` -> `Resolving and preparing N blocks...`
- `BlockPreparationStarted` -> `Preparing i/N: <block_id>`
- `BlockApplyStarted` -> `Applying i/N: <block_id>`
- `BlockDependencyInputsStarted` -> `Resolving dependency inputs for i/N: <block_id>`
- `BlockApplyCompleted` -> durable line `Applied i/N: <block_id>`
- `ProvisioningFailed` -> durable line `Failed during <phase>: <block_id>`

Recommended mapping for forget:

- `DestroyStarted` -> `Destroying N blocks...`
- `BlockDestroyStarted` -> `Destroying i/N: <block_id>`
- `BlockDestroyCompleted` -> durable line `Destroyed i/N: <block_id>`
- `BlockDestroyFailed` -> durable line `Failed destroy i/N: <block_id>`

Do not print outputs in the first iteration. That would overload the terminal and is
not needed to solve the progress visibility problem.

## 7. Renderer Behavior Rules

The project UI renderer should:

- start status rendering before consuming the first event
- update the live status for transient events
- print permanent lines only for meaningful milestones or failures
- stop the live status cleanly on success and on exception

Do not buffer all events before rendering. It must consume the iterator lazily.

## 8. Tests For Step 2

Update `tests/test_project_feature.py` with these cases:

### Application streaming wrapper

Assert that `provision_project_events(folder)` loads the manifest and forwards the
iterator from the gateway.

### CLI provision uses streaming path

Monkeypatch:

- `application.provision_project_events`
- the renderer function in `project.ui.progress`

Assert:

- the CLI command exits zero
- the renderer received the iterator
- the final success line is still printed

### CLI forget uses streaming path

Mirror the same test for `forget`.

## 9. Done Criteria For Step 2

This step is done when:

- project has iterator-based application APIs for provision and forget
- the gateway forwards block event streams without draining them
- the CLI consumes the stream through a dedicated project UI progress module
- final success and existing error handling remain intact