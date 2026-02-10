from dataclasses import dataclass
from typing import Any, Callable

from freeloader.pipeline.dag import ResolvedBlock
from freeloader.pipeline.orchestrator import Orchestrator
from freeloader.projects.models import ProjectManifest


@dataclass(frozen=True)
class PlanBlock:
    block_id: str
    layer: str
    runner: str
    depends_on: list[str]


@dataclass(frozen=True)
class BlockPlanOutput:
    block_id: str
    output: str


@dataclass(frozen=True)
class PlanResult:
    project_name: str
    blocks: list[PlanBlock]
    plan_outputs: list[BlockPlanOutput]


@dataclass(frozen=True)
class ApplyResult:
    project_name: str
    outputs: dict[str, dict[str, Any]]


@dataclass(frozen=True)
class DestroyResult:
    project_name: str


def _to_plan_blocks(resolved: list[ResolvedBlock]) -> list[PlanBlock]:
    return [
        PlanBlock(
            block_id=b.ref.resolved_id,
            layer=b.contract.block.layer.value,
            runner=b.contract.block.runner.value,
            depends_on=sorted(b.inputs.values()) if b.inputs else [],
        )
        for b in resolved
    ]


class ApplyUseCases:
    def __init__(self, orchestrator: Orchestrator) -> None:
        self._orchestrator = orchestrator

    def plan(self, manifest: ProjectManifest) -> PlanResult:
        resolved = self._orchestrator.resolve(manifest)
        return PlanResult(
            project_name=manifest.project.name,
            blocks=_to_plan_blocks(resolved),
            plan_outputs=[],
        )

    def detailed_plan(self, manifest: ProjectManifest) -> PlanResult:
        resolved = self._orchestrator.resolve(manifest)
        plan_pairs = self._orchestrator.plan(manifest)
        plan_outputs = [
            BlockPlanOutput(block_id=bid, output=out)
            for bid, out in plan_pairs
        ]
        return PlanResult(
            project_name=manifest.project.name,
            blocks=_to_plan_blocks(resolved),
            plan_outputs=plan_outputs,
        )

    def apply(
        self,
        manifest: ProjectManifest,
        *,
        on_plan: Callable[[str, str], None] | None = None,
        on_apply: Callable[[str, dict[str, Any]], None] | None = None,
        on_skip: Callable[[str], None] | None = None,
    ) -> ApplyResult:
        results = self._orchestrator.apply(
            manifest, on_plan=on_plan, on_apply=on_apply, on_skip=on_skip)
        outputs = {r.block_id: r.outputs for r in results}
        return ApplyResult(project_name=manifest.project.name, outputs=outputs)

    def destroy(
        self,
        manifest: ProjectManifest,
        *,
        on_block: Callable[[str], None] | None = None,
    ) -> DestroyResult:
        self._orchestrator.destroy(manifest, on_block=on_block)
        return DestroyResult(project_name=manifest.project.name)
