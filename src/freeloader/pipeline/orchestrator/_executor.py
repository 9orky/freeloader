from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Callable

from freeloader.pipeline.context import ExecutionContext
from freeloader.pipeline.dag import ResolvedBlock
from freeloader.pipeline.orchestrator._resumption import ResumptionManager
from freeloader.pipeline.policies import check_block_feasibility
from freeloader.pipeline.progress import ProgressStatus
from freeloader.projects.models import BlockStatus, ProjectManifest

if TYPE_CHECKING:
    from freeloader.pipeline.runners import RunnerRegistry
    from freeloader.projects.state import StateManager


@dataclass(frozen=True)
class BlockResult:
    block_id: str
    outputs: dict[str, Any]


class PipelineExecutor:
    def __init__(
        self,
        runner_registry: "RunnerRegistry",
        state_manager: "StateManager",
        resumption: ResumptionManager,
    ) -> None:
        self._runners = runner_registry
        self._state_manager = state_manager
        self._resumption = resumption

    def plan(
        self,
        resolved: list[ResolvedBlock],
        *,
        on_block: Callable[[str, str], None] | None = None,
    ) -> list[tuple[str, str]]:
        context = ExecutionContext()
        results: list[tuple[str, str]] = []
        for block in resolved:
            runner = self._runners.get(block.contract.block.runner)
            check_block_feasibility(block, runner)
            output = runner.plan_block(block, context)
            results.append((block.ref.resolved_id, output))
            if on_block:
                on_block(block.ref.resolved_id, output)
        return results

    def apply(
        self,
        resolved: list[ResolvedBlock],
        manifest: ProjectManifest,
        *,
        on_plan: Callable[[str, str], None] | None = None,
        on_apply: Callable[[str, dict[str, Any]], None] | None = None,
        on_skip: Callable[[str], None] | None = None,
    ) -> list[BlockResult]:
        self._resumption.load_or_create(manifest, "apply", resolved)
        context = self._resumption.restore_context()
        state = self._state_manager.load()
        results: list[BlockResult] = []

        for block in resolved:
            block_id = block.ref.resolved_id
            bp = self._resumption.find_block_progress(block_id)

            if bp.status == ProgressStatus.applied:
                if on_skip:
                    on_skip(block_id)
                continue

            runner = self._runners.get(block.contract.block.runner)
            check_block_feasibility(block, runner)

            try:
                plan_output = runner.plan_block(block, context)
                self._resumption.mark_planned(block_id)
                if on_plan:
                    on_plan(block_id, plan_output)

                outputs = runner.apply_block(block, context)
                context.set_outputs(block_id, outputs)
                self._resumption.mark_applied(block_id)

                state = self._state_manager.update_block(
                    state, block_id, block.contract.block.name,
                    BlockStatus.created, outputs=outputs,
                )

                results.append(BlockResult(block_id=block_id, outputs=outputs))
                if on_apply:
                    on_apply(block_id, outputs)

            except Exception as exc:
                self._resumption.mark_failed(block_id, str(exc))
                state = self._state_manager.update_block(
                    state, block_id, block.contract.block.name,
                    BlockStatus.failed, error=str(exc),
                )
                self._state_manager.save(state)
                raise

        state = state.model_copy(
            update={"last_up": datetime.now(timezone.utc)})
        self._state_manager.save(state)
        self._resumption.clear(manifest.project.name)
        return results

    def destroy(
        self,
        resolved: list[ResolvedBlock],
        manifest: ProjectManifest,
        *,
        on_block: Callable[[str], None] | None = None,
    ) -> None:
        self._resumption.load_or_create(
            manifest, "destroy", list(reversed(resolved)))
        state = self._state_manager.load()
        context = ExecutionContext()

        for bs in state.blocks:
            context.set_outputs(bs.block_name, bs.outputs)

        for block in reversed(resolved):
            block_id = block.ref.resolved_id
            bp = self._resumption.find_block_progress(block_id)

            if bp.status == ProgressStatus.applied:
                continue

            runner = self._runners.get(block.contract.block.runner)

            try:
                runner.destroy_block(block, context)
                self._resumption.mark_applied(block_id)
                state = self._state_manager.update_block(
                    state, block_id, block.contract.block.name,
                    BlockStatus.destroyed,
                )
                if on_block:
                    on_block(block_id)
            except Exception as exc:
                self._resumption.mark_failed(block_id, str(exc))
                self._state_manager.save(state)
                raise

        state = state.model_copy(
            update={"last_down": datetime.now(timezone.utc)})
        self._state_manager.save(state)
        self._resumption.clear(manifest.project.name)
