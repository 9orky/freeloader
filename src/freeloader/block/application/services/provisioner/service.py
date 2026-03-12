from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from freeloader.block.domain.entity import BlockRef
from freeloader.block.domain.events import (
    BlockDestroyEvent,
    BlockProvisionEvent,
    DestroyFinished,
    DestroyStarted,
    ProvisioningFinished,
    ProvisioningStarted,
)
from freeloader.block.domain.provisioning import (
    DestroyReport,
    ProvisioningPlan,
    ProvisioningReport,
)
from freeloader.block.domain.repository import BlockRepository
from freeloader.block.infrastructure.runner import BlockRunner

from .apply import ProvisioningApplyStage
from .context import ExecutionOutputs
from .destroy import DestroyStage
from .planner import ProvisioningPlanBuilder
from .prepare import ProvisioningPreparationStage


class BlockProvisioningService:
    """Orchestrates block provisioning and destroy flows."""

    def __init__(self, repository: BlockRepository, runner: BlockRunner) -> None:
        self._repository = repository
        self._runner = runner

    def build_plan(self, block_refs: list[BlockRef]) -> ProvisioningPlan:
        return ProvisioningPlanBuilder(self._repository).build(block_refs)

    def provision(
        self, resources_root: Path, block_refs: list[BlockRef]
    ) -> ProvisioningReport:
        report: ProvisioningReport | None = None
        for event in self.provision_events(resources_root, block_refs):
            if isinstance(event, ProvisioningFinished):
                report = event.report
        assert report is not None
        return report

    def provision_events(
        self, resources_root: Path, block_refs: list[BlockRef]
    ) -> Iterator[BlockProvisionEvent]:
        plan = self.build_plan(block_refs)
        preparation = ProvisioningPreparationStage(
            self._repository, self._runner)
        apply = ProvisioningApplyStage(self._runner, ExecutionOutputs())

        yield ProvisioningStarted(total_blocks=len(plan.steps), block_ids=plan.block_ids)
        yield from preparation.run(plan, resources_root)
        yield from apply.run(plan, preparation.resources)

        report = ProvisioningReport(
            plan=plan, applied_steps=apply.applied_steps)
        yield ProvisioningFinished(report=report)

    def destroy(
        self, resources_root: Path, block_refs: list[BlockRef]
    ) -> DestroyReport:
        report: DestroyReport | None = None
        for event in self.destroy_events(resources_root, block_refs):
            if isinstance(event, DestroyFinished):
                report = event.report
        assert report is not None
        return report

    def destroy_events(
        self, resources_root: Path, block_refs: list[BlockRef]
    ) -> Iterator[BlockDestroyEvent]:
        plan = self.build_plan(block_refs)
        destroy = DestroyStage(self._runner)

        yield DestroyStarted(total_blocks=len(plan.steps), block_ids=plan.block_ids)
        yield from destroy.run(plan, resources_root)

        report = DestroyReport(plan=plan, steps=destroy.steps)
        yield DestroyFinished(report=report)
