from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from freeloader.block.domain.events import (
    BlockPreparationCompleted,
    BlockPreparationStarted,
    BlockProvisionEvent,
    ProvisioningFailed,
)
from freeloader.block.domain.provisioning import ProvisioningPlan
from freeloader.block.domain.repository import BlockRepository
from freeloader.block.infrastructure.resource import ProvisioningResource
from freeloader.block.infrastructure.runner import BlockRunner


class ProvisioningPreparationStage:
    def __init__(self, repository: BlockRepository, runner: BlockRunner) -> None:
        self._repository = repository
        self._runner = runner
        self._resources: dict[str, ProvisioningResource] = {}

    @property
    def resources(self) -> dict[str, ProvisioningResource]:
        return self._resources

    def run(
        self,
        plan: ProvisioningPlan,
        resources_root: Path,
    ) -> Iterator[BlockProvisionEvent]:
        self._resources = {}
        total = len(plan.steps)
        for index, step in enumerate(plan.steps, start=1):
            yield BlockPreparationStarted(block_id=step.id, index=index, total=total)
            resource = ProvisioningResource(resources_root / step.id)
            try:
                self._repository.dump_assets(step.block.id, resource.folder)
                self._runner.run_init(resource, step.resolved_block)
                self._runner.run_plan(resource)
            except Exception as error:
                yield ProvisioningFailed(
                    block_id=step.id,
                    phase="prepare",
                    error=str(error),
                )
                raise
            self._resources[step.id] = resource
            yield BlockPreparationCompleted(block_id=step.id, index=index, total=total)
