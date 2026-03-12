from __future__ import annotations

from collections.abc import Iterator

from freeloader.block.domain.entity import OutputReference
from freeloader.block.domain.events import (
    BlockApplyCompleted,
    BlockApplyStarted,
    BlockDependencyInputsStarted,
    BlockProvisionEvent,
    ProvisioningFailed,
)
from freeloader.block.domain.provisioning import AppliedStepReport, ProvisioningPlan
from freeloader.block.infrastructure.resource import ProvisioningResource
from freeloader.block.infrastructure.runner import BlockRunner

from .context import ExecutionOutputs


class ProvisioningApplyStage:
    def __init__(self, runner: BlockRunner, outputs: ExecutionOutputs) -> None:
        self._runner = runner
        self._outputs = outputs
        self._applied_steps: list[AppliedStepReport] = []

    @property
    def applied_steps(self) -> list[AppliedStepReport]:
        return self._applied_steps

    def run(
        self,
        plan: ProvisioningPlan,
        resources: dict[str, ProvisioningResource],
    ) -> Iterator[BlockProvisionEvent]:
        self._applied_steps = []
        total = len(plan.steps)
        for index, step in enumerate(plan.steps, start=1):
            resource = resources[step.id]
            yield BlockApplyStarted(
                block_id=step.id,
                index=index,
                total=total,
                has_dependency_inputs=step.has_inputs,
            )

            if step.has_inputs:
                try:
                    yield BlockDependencyInputsStarted(
                        block_id=step.id,
                        index=index,
                        total=total,
                        provider_ids=self._provider_ids(
                            step.resolved_block.inputs),
                    )
                    extra_vars = self._outputs.resolve_inputs(
                        step.resolved_block.inputs)
                    self._runner.run_init(
                        resource, step.resolved_block, extra_vars)
                    self._runner.run_plan(resource)
                except Exception as error:
                    yield ProvisioningFailed(
                        block_id=step.id,
                        phase="dependency_inputs",
                        error=str(error),
                    )
                    raise

            try:
                output = self._runner.run_apply(resource)
            except Exception as error:
                yield ProvisioningFailed(
                    block_id=step.id,
                    phase="apply",
                    error=str(error),
                )
                raise

            self._outputs.set_outputs(step.id, output)
            self._applied_steps.append(
                AppliedStepReport(
                    block_id=step.id,
                    outputs=output,
                    had_dependency_inputs=step.has_inputs,
                )
            )
            yield BlockApplyCompleted(
                block_id=step.id,
                index=index,
                total=total,
                outputs=output,
            )

    def _provider_ids(self, inputs: list[OutputReference]) -> list[str]:
        provider_ids: list[str] = []
        for ref in inputs:
            if ref.provider_id not in provider_ids:
                provider_ids.append(ref.provider_id)
        return provider_ids
