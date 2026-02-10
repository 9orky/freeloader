from dataclasses import dataclass
from typing import Any, Callable

from freeloader.pipeline.orchestrator import Orchestrator, ExecutionPlan
from freeloader.projects.models import ProjectManifest


@dataclass(frozen=True)
class PlanBlock:
    block_id: str
    layer: str
    runner: str
    depends_on: list[str]


@dataclass(frozen=True)
class PlanResult:
    project_name: str
    blocks: list[PlanBlock]


@dataclass(frozen=True)
class RunnerPlanOutput:
    runner: str
    output: str


@dataclass(frozen=True)
class DetailedPlanResult:
    project_name: str
    blocks: list[PlanBlock]
    runner_outputs: list[RunnerPlanOutput]


@dataclass(frozen=True)
class ApplyResult:
    project_name: str
    outputs: dict[str, dict[str, Any]]


@dataclass(frozen=True)
class DestroyResult:
    project_name: str


class ApplyUseCases:
    def __init__(self, orchestrator: Orchestrator) -> None:
        self._orchestrator = orchestrator

    def plan(self, manifest: ProjectManifest) -> PlanResult:
        execution_plan = self._orchestrator.plan(manifest)
        blocks = self._extract_plan_blocks(execution_plan)
        return PlanResult(project_name=execution_plan.project_name, blocks=blocks)

    def detailed_plan(self, manifest: ProjectManifest) -> DetailedPlanResult:
        execution_plan = self._orchestrator.detailed_plan(manifest)
        blocks = self._extract_plan_blocks(execution_plan)
        runner_outputs = [
            RunnerPlanOutput(runner=g.runner_type.value, output=g.plan_output)
            for g in execution_plan.groups
            if g.plan_output
        ]
        return DetailedPlanResult(
            project_name=execution_plan.project_name,
            blocks=blocks,
            runner_outputs=runner_outputs,
        )

    def _extract_plan_blocks(self, execution_plan: ExecutionPlan) -> list[PlanBlock]:
        blocks: list[PlanBlock] = []
        for group in execution_plan.groups:
            for block in group.blocks:
                deps = sorted(block.inputs.values()) if block.inputs else []
                blocks.append(PlanBlock(
                    block_id=block.ref.resolved_id,
                    layer=block.contract.block.layer.value,
                    runner=group.runner_type.value,
                    depends_on=deps,
                ))
        return blocks

    def apply(self, manifest: ProjectManifest) -> ApplyResult:
        outputs = self._orchestrator.apply(manifest)
        return ApplyResult(project_name=manifest.project.name, outputs=outputs)

    def destroy(
        self,
        manifest: ProjectManifest,
        *,
        on_block: Callable[[str], None] | None = None,
    ) -> DestroyResult:
        self._orchestrator.destroy(manifest, on_block=on_block)
        return DestroyResult(project_name=manifest.project.name)
