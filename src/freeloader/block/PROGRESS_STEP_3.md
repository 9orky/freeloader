# Progress Step 3: Shared Console Implementation

## Scope

This step adds the reusable terminal rendering primitive needed by the project UI.
It should stay generic enough for future streaming CLI workflows, but it should not
take ownership of project-specific wording or block-specific event semantics.

The shared console layer owns the mechanics of:

- opening a live Rich status spinner
- updating transient text
- printing durable lines while the spinner is active
- shutting down the live view cleanly on success or failure

The project UI layer still owns message mapping.

## Outcome

After this step, the repository has a dedicated console progress helper file that can
be reused by any CLI command with a streaming event source.

Recommended file:

- `src/freeloader/shared/console/progress.py`

This is the dedicated Python file requested for progress rendering concerns.

## Files To Add

- `src/freeloader/shared/console/progress.py`

## Files To Change

- `src/freeloader/shared/console/__init__.py`

## 1. Why A Dedicated File Is Necessary

Without a dedicated file, the new project UI progress flow will become a mixture of:

- Rich status management
- printing logic
- exception-safe cleanup
- event message mapping

all inside one CLI command.

That would make `project/ui/cli.py` noisy and hard to test.

The dedicated shared file should isolate the Rich control flow so feature-specific UI
code can stay small and readable.

## 2. Boundary For The Shared Helper

`shared/console/progress.py` should be generic. It should not import block or project
types.

It should operate on already formatted messages and optional callbacks.

Recommended boundary:

- shared console helper manages the live terminal machinery
- project UI adapter decides what message to show for each event

This separation keeps `shared` free from feature-specific concepts.

## 3. Recommended API

Use a small context-managed controller class plus one convenience runner function.

Recommended API:

```python
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class ProgressUpdate:
    status: str | None = None
    line: str | None = None


class StatusStream:
    def __init__(self, initial_status: str = "Working...") -> None:
        ...

    def __enter__(self) -> "StatusStream":
        ...

    def __exit__(self, exc_type, exc, tb) -> None:
        ...

    def update(self, message: str) -> None:
        ...

    def write_line(self, message: str, *, style: str | None = None) -> None:
        ...


def run_status_stream(
    events: Iterable[T],
    *,
    initial_status: str,
    on_event: Callable[[T], ProgressUpdate | None],
) -> None:
    ...
```

Rationale:

- `StatusStream` owns the Rich context manager and direct console access
- `ProgressUpdate` gives the caller a small return shape for transient status plus
  optional durable line output
- `run_status_stream(...)` keeps caller code short for the common pattern

## 4. Rich Implementation Details

Use the existing shared console `_console` instance from `shared/console/__init__.py`.
Do not create a second long-lived global console in the new file unless Rich requires
it for a specific feature.

Suggested implementation pattern:

```python
class StatusStream:
    def __enter__(self) -> "StatusStream":
        self._status = _console.status(self._initial_status)
        self._status.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        assert self._status is not None
        self._status.__exit__(exc_type, exc, tb)

    def update(self, message: str) -> None:
        assert self._status is not None
        self._status.update(message)

    def write_line(self, message: str, *, style: str | None = None) -> None:
        _console.print(message, style=style)
```

Important detail:

- validate that printing lines while the status spinner is active behaves cleanly in
  the current Rich version already installed through `pyproject.toml`

If Rich output interleaving is messy, fall back to stopping the status temporarily,
printing the line, and re-entering a new status context with the last message.

## 5. Recommended Export Strategy

Update `shared/console/__init__.py` to re-export the new shared helper:

- `ProgressUpdate`
- `StatusStream`
- `run_status_stream`

Keep the existing public functions unchanged.

## 6. How Project UI Should Use It

The project UI adapter in `project/ui/progress.py` should be able to do this:

```python
def render_project_provision_progress(events: Iterable[BlockProvisionEvent]) -> None:
    run_status_stream(
        events,
        initial_status="Starting provisioning...",
        on_event=_map_provision_event,
    )
```

Where `_map_provision_event` is project-owned and returns `ProgressUpdate` values.

Example mapping return values:

- status-only update:

```python
ProgressUpdate(status="Preparing 1/3: git.repo")
```

- durable line plus next status:

```python
ProgressUpdate(
    status="Applying 2/3: docker.image",
    line="✓ Applied 1/3: git.repo",
)
```

This keeps message authorship in project UI while reusing the same rendering engine.

## 7. Testing Strategy For Step 3

The repository does not currently have focused console unit tests, so keep tests light
and behavior-oriented.

Recommended test level:

- project CLI tests remain the main end-to-end proof that the helper works in practice
- if a direct unit test is added for `run_status_stream`, keep it minimal and avoid
  brittle Rich internals assertions

Useful direct assertion if tested:

- `on_event` is called lazily in order for each event in the iterable

Do not over-invest in terminal rendering internals in this step.

## 8. Done Criteria For Step 3

This step is done when:

- `shared/console/progress.py` exists as the dedicated reusable progress helper
- project UI can render a stream through that helper without embedding Rich control
  flow directly in the CLI command
- shared console stays generic and does not depend on block or project types