from __future__ import annotations

from collections.abc import Iterable

from freeloader.block import (
    BlockApplyCompleted,
    BlockApplyStarted,
    BlockDependencyInputsStarted,
    BlockDestroyCompleted,
    BlockDestroyEvent,
    BlockDestroyFailed,
    BlockDestroyStarted,
    BlockPreparationStarted,
    BlockProvisionEvent,
    DestroyFinished,
    DestroyStarted,
    ProvisioningFailed,
    ProvisioningFinished,
    ProvisioningStarted,
)
from freeloader.shared.console import ProgressUpdate, run_status_stream


def render_project_provision_progress(events: Iterable[BlockProvisionEvent]) -> None:
    run_status_stream(
        events,
        initial_status="Starting provisioning...",
        on_event=_map_provision_event,
    )


def render_project_forget_progress(events: Iterable[BlockDestroyEvent]) -> None:
    run_status_stream(
        events,
        initial_status="Starting destroy...",
        on_event=_map_forget_event,
    )


def _map_provision_event(event: BlockProvisionEvent) -> ProgressUpdate | None:
    if isinstance(event, ProvisioningStarted):
        return ProgressUpdate(
            status=f"Resolving and preparing {event.total_blocks} blocks..."
        )
    if isinstance(event, BlockPreparationStarted):
        return ProgressUpdate(
            status=f"Preparing {event.index}/{event.total}: {event.block_id}"
        )
    if isinstance(event, BlockApplyStarted):
        return ProgressUpdate(
            status=f"Applying {event.index}/{event.total}: {event.block_id}"
        )
    if isinstance(event, BlockDependencyInputsStarted):
        return ProgressUpdate(
            status=(
                f"Resolving dependency inputs for {event.index}/{event.total}: "
                f"{event.block_id}"
            )
        )
    if isinstance(event, BlockApplyCompleted):
        return ProgressUpdate(
            line=f"Applied {event.index}/{event.total}: {event.block_id}",
            style="green",
        )
    if isinstance(event, ProvisioningFailed):
        message = f"Failed during {event.phase}: {event.block_id}"
        return ProgressUpdate(status=message, line=message, style="red")
    if isinstance(event, ProvisioningFinished):
        return None
    return None


def _map_forget_event(event: BlockDestroyEvent) -> ProgressUpdate | None:
    if isinstance(event, DestroyStarted):
        return ProgressUpdate(status=f"Destroying {event.total_blocks} blocks...")
    if isinstance(event, BlockDestroyStarted):
        return ProgressUpdate(
            status=f"Destroying {event.index}/{event.total}: {event.block_id}"
        )
    if isinstance(event, BlockDestroyCompleted):
        return ProgressUpdate(
            line=f"Destroyed {event.index}/{event.total}: {event.block_id}",
            style="green",
        )
    if isinstance(event, BlockDestroyFailed):
        message = f"Failed destroy {event.index}/{event.total}: {event.block_id}"
        return ProgressUpdate(status=message, line=message, style="red")
    if isinstance(event, DestroyFinished):
        return None
    return None
