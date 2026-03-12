from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from freeloader.block.domain.events import (
    BlockDestroyCompleted,
    BlockDestroyEvent,
    BlockDestroyFailed,
    BlockDestroyStarted,
)
from freeloader.block.domain.provisioning import DestroyStepReport, ProvisioningPlan
from freeloader.block.infrastructure.resource import ProvisioningResource
from freeloader.block.infrastructure.runner import BlockRunner


class DestroyStage:
    def __init__(self, runner: BlockRunner) -> None:
        self._runner = runner
        self._steps: list[DestroyStepReport] = []

    @property
    def steps(self) -> list[DestroyStepReport]:
        return self._steps

    def run(
        self,
        plan: ProvisioningPlan,
        resources_root: Path,
    ) -> Iterator[BlockDestroyEvent]:
        self._steps = []
        total = len(plan.steps)
        for index, step in enumerate(reversed(plan.steps), start=1):
            resource: ProvisioningResource | None = None
            yield BlockDestroyStarted(block_id=step.id, index=index, total=total)
            try:
                resource = ProvisioningResource(resources_root / step.id)
                self._runner.run_destroy(resource)
                self._steps.append(DestroyStepReport(
                    block_id=step.id, destroyed=True))
                yield BlockDestroyCompleted(block_id=step.id, index=index, total=total)
            except Exception as error:
                self._steps.append(
                    DestroyStepReport(
                        block_id=step.id,
                        destroyed=False,
                        error=str(error),
                    )
                )
                yield BlockDestroyFailed(
                    block_id=step.id,
                    index=index,
                    total=total,
                    error=str(error),
                )
            finally:
                if resource is not None:
                    resource.rm()
