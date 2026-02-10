from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Callable

from freeloader.pipeline.context import ExecutionContext
from freeloader.pipeline.dag import DAGResolver, ResolvedBlock
from freeloader.pipeline.policies import validate_manifest_blocks, check_secrets, check_all_runners_feasibility
from freeloader.blocks.models import RunnerType
from freeloader.projects.models import ProjectManifest, BlockStatus
from freeloader.shared.errors import ConfigurationError

if TYPE_CHECKING:
    from freeloader.blocks.registry import BlockRegistry
    from freeloader.credentials.vault import SecretVault
    from freeloader.pipeline.runners import RunnerRegistry
    from freeloader.projects.config import GlobalConfig
    from freeloader.projects.state import StateManager


@dataclass
class ExecutionGroup:
    runner_type: RunnerType
    blocks: list[ResolvedBlock]
    plan_output: str = ""


@dataclass
class ExecutionPlan:
    groups: list[ExecutionGroup] = field(default_factory=list)
    project_name: str = ""


RUNNER_ORDER: dict[RunnerType, int] = {
    RunnerType.terraform: 0,
    RunnerType.api: 1,
    RunnerType.generator: 2,
    RunnerType.script: 3,
}


class Orchestrator:
    def __init__(
        self,
        dag_resolver: DAGResolver,
        runner_registry: "RunnerRegistry",
        state_manager: "StateManager",
        vault: "SecretVault",
        config: "GlobalConfig",
        block_registry: "BlockRegistry",
    ) -> None:
        self._dag = dag_resolver
        self._runners = runner_registry
        self._state_manager = state_manager
        self._vault = vault
        self._config = config
        self._blocks = block_registry

    def plan(self, manifest: ProjectManifest) -> ExecutionPlan:
        contracts = validate_manifest_blocks(manifest.blocks, self._blocks)
        resolved = self._dag.resolve(manifest.blocks, contracts)
        groups = self._group_by_runner(resolved)
        return ExecutionPlan(groups=groups, project_name=manifest.project.name)

    def detailed_plan(self, manifest: ProjectManifest) -> ExecutionPlan:
        missing = check_secrets(manifest, self._blocks, self._vault)
        if missing:
            raise ConfigurationError(
                f"Missing secrets: {', '.join(missing)}\n"
                "Run 'fl credentials add-provider <provider>' to configure them."
            )

        plan = self.plan(manifest)
        check_all_runners_feasibility(plan.groups, self._runners)

        context = ExecutionContext()
        detailed_groups: list[ExecutionGroup] = []
        for group in plan.groups:
            runner = self._runners.get(group.runner_type)
            output = runner.plan(group.blocks, context)
            detailed_groups.append(ExecutionGroup(
                runner_type=group.runner_type,
                blocks=group.blocks,
                plan_output=output,
            ))
        return ExecutionPlan(groups=detailed_groups, project_name=plan.project_name)

    def apply(self, manifest: ProjectManifest) -> dict[str, dict[str, Any]]:
        missing = check_secrets(manifest, self._blocks, self._vault)
        if missing:
            raise ConfigurationError(
                f"Missing secrets: {', '.join(missing)}\n"
                "Run 'fl credentials add-provider <provider>' to configure them."
            )

        plan = self.plan(manifest)
        check_all_runners_feasibility(plan.groups, self._runners)

        context = ExecutionContext()
        state = self._state_manager.load()
        all_outputs: dict[str, dict[str, Any]] = {}

        for group in plan.groups:
            runner = self._runners.get(group.runner_type)
            outputs = runner.apply(group.blocks, context)
            for block_id, block_outputs in outputs.items():
                context.set_outputs(block_id, block_outputs)
                all_outputs[block_id] = block_outputs
                block_ref = next(
                    b for b in group.blocks if b.ref.resolved_id == block_id)
                state = self._state_manager.update_block(
                    state, block_id, block_ref.contract.block.name,
                    BlockStatus.created, outputs=block_outputs,
                )

        state = state.model_copy(
            update={"last_up": datetime.now(timezone.utc)})
        self._state_manager.save(state)
        return all_outputs

    def destroy(
        self,
        manifest: ProjectManifest,
        *,
        on_block: Callable[[str], None] | None = None,
    ) -> None:
        plan = self.plan(manifest)
        check_all_runners_feasibility(plan.groups, self._runners)

        context = ExecutionContext()
        state = self._state_manager.load()

        for bs in state.blocks:
            context.set_outputs(bs.block_name, bs.outputs)

        for group in reversed(plan.groups):
            runner = self._runners.get(group.runner_type)
            for block in reversed(group.blocks):
                runner.destroy([block], context)
                block_id = block.ref.resolved_id
                state = self._state_manager.update_block(
                    state, block_id, block.contract.block.name,
                    BlockStatus.destroyed,
                )
                if on_block:
                    on_block(block_id)

        state = state.model_copy(
            update={"last_down": datetime.now(timezone.utc)})
        self._state_manager.save(state)

    def _group_by_runner(self, resolved: list[ResolvedBlock]) -> list[ExecutionGroup]:
        groups_map: dict[RunnerType, list[ResolvedBlock]] = defaultdict(list)
        for block in resolved:
            groups_map[block.contract.block.runner].append(block)

        return [
            ExecutionGroup(runner_type=rt, blocks=blocks)
            for rt, blocks in sorted(groups_map.items(), key=lambda x: RUNNER_ORDER.get(x[0], 99))
        ]
