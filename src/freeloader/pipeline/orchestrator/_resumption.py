from freeloader.pipeline.context import ExecutionContext
from freeloader.pipeline.dag import ResolvedBlock
from freeloader.pipeline.progress import BlockProgress, ProgressStatus, ProgressTracker
from freeloader.projects.models import ProjectManifest

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from freeloader.projects.state import StateManager


class ResumptionManager:
    def __init__(
        self,
        progress_tracker: ProgressTracker,
        state_manager: "StateManager",
    ) -> None:
        self._progress = progress_tracker
        self._state_manager = state_manager

    def load_or_create(
        self,
        manifest: ProjectManifest,
        action: str,
        resolved: list[ResolvedBlock],
    ) -> None:
        existing = self._progress.load(manifest.project.name)
        if existing and existing.action == action:
            self._current = existing
            return
        block_progresses = [
            BlockProgress(
                block_id=b.ref.resolved_id,
                block_use=b.contract.block.name,
                runner=b.contract.block.runner.value,
            )
            for b in resolved
        ]
        self._current = self._progress.create(
            manifest.project.name, action, block_progresses)

    def find_block_progress(self, block_id: str) -> BlockProgress:
        return next(bp for bp in self._current.blocks if bp.block_id == block_id)

    def restore_context(self) -> ExecutionContext:
        context = ExecutionContext()
        state = self._state_manager.load()
        applied_ids = {
            bp.block_id for bp in self._current.blocks if bp.status == ProgressStatus.applied}
        for bs in state.blocks:
            if bs.block_name in applied_ids and bs.outputs:
                context.set_outputs(bs.block_name, bs.outputs)
        return context

    def mark_planned(self, block_id: str) -> None:
        self._current = self._progress.mark_planned(self._current, block_id)

    def mark_applied(self, block_id: str) -> None:
        self._current = self._progress.mark_applied(self._current, block_id)

    def mark_failed(self, block_id: str, error: str) -> None:
        self._current = self._progress.mark_failed(
            self._current, block_id, error)

    def clear(self, project_name: str) -> None:
        self._progress.clear(project_name)
        self._current = None
