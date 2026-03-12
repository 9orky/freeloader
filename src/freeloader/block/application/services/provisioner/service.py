from __future__ import annotations

from pathlib import Path

from freeloader.shared.types import ConfigValue

from ....domain.entity import BlockRef, OutputReference
from ....domain.repository import BlockRepository
from ....domain.resolver import DAGResolver
from ....domain.value_object import BlockId
from ....infrastructure.resource import ProvisioningResource
from ....infrastructure.runner import BlockRunner

from .models import (
    AppliedStepReport,
    DestroyReport,
    DestroyStepReport,
    ProvisioningPlan,
    ProvisioningReport,
    ProvisioningStep,
)


class _ExecutionContext:
    """Accumulates block outputs during the provisioning loop."""

    def __init__(self) -> None:
        self._outputs: dict[str, dict[str, ConfigValue | None]] = {}

    def set_outputs(self, block_id: str, outputs: dict[str, ConfigValue | None]) -> None:
        self._outputs[block_id] = outputs

    def resolve_inputs(
        self, inputs: list[OutputReference]
    ) -> dict[str, ConfigValue | None]:
        result: dict[str, ConfigValue | None] = {}
        for ref in inputs:
            tfvar_name = ref.requirement_key.replace(".", "_")
            result[tfvar_name] = self._outputs.get(ref.provider_id, {}).get(
                ref.output_name
            )
        return result


class BlockProvisioningService:
    """Orchestrates block provisioning and destroy flows."""

    def __init__(self, repository: BlockRepository, runner: BlockRunner) -> None:
        self._repository = repository
        self._runner = runner

    def build_plan(self, block_refs: list[BlockRef]) -> ProvisioningPlan:
        assert block_refs, "At least one block reference must be provided"
        block_ids = [BlockId(ref.resolved_id) for ref in block_refs]
        blocks = self._repository.load_by_ids(block_ids)
        contracts = {block_id: block.contract for block_id,
                     block in blocks.items()}
        resolved_blocks = DAGResolver().resolve(block_refs, contracts)
        return ProvisioningPlan(
            steps=[
                ProvisioningStep(
                    block=blocks[resolved_block.id], resolved_block=resolved_block)
                for resolved_block in resolved_blocks
            ]
        )

    def provision(
        self, resources_root: Path, block_refs: list[BlockRef]
    ) -> ProvisioningReport:
        plan = self.build_plan(block_refs)
        context = _ExecutionContext()
        resources = self._prepare_resources(plan, resources_root)
        applied_steps: list[AppliedStepReport] = []

        for step in plan.steps:
            resource = resources[step.id]
            if step.has_inputs:
                extra_vars = context.resolve_inputs(step.resolved_block.inputs)
                self._runner.run_init(
                    resource, step.resolved_block, extra_vars)
                self._runner.run_plan(resource)

            output = self._runner.run_apply(resource)
            context.set_outputs(step.id, output)
            applied_steps.append(
                AppliedStepReport(
                    block_id=step.id,
                    outputs=output,
                    had_dependency_inputs=step.has_inputs,
                )
            )

        return ProvisioningReport(plan=plan, applied_steps=applied_steps)

    def destroy(
        self, resources_root: Path, block_refs: list[BlockRef]
    ) -> DestroyReport:
        plan = self.build_plan(block_refs)
        steps: list[DestroyStepReport] = []

        for step in reversed(plan.steps):
            resource: ProvisioningResource | None = None
            try:
                resource_folder = resources_root / step.id
                resource = ProvisioningResource(resource_folder)
                self._runner.run_destroy(resource)
                steps.append(DestroyStepReport(
                    block_id=step.id, destroyed=True))
            except Exception as error:
                steps.append(
                    DestroyStepReport(
                        block_id=step.id,
                        destroyed=False,
                        error=str(error),
                    )
                )
            finally:
                if resource is not None:
                    resource.rm()

        return DestroyReport(plan=plan, steps=steps)

    def _prepare_resources(
        self,
        plan: ProvisioningPlan,
        resources_root: Path,
    ) -> dict[str, ProvisioningResource]:
        resources: dict[str, ProvisioningResource] = {}
        for step in plan.steps:
            resource_folder = resources_root / step.id
            resource = ProvisioningResource(resource_folder)
            self._repository.dump_assets(step.block.id, resource.folder)
            self._runner.run_init(resource, step.resolved_block)
            self._runner.run_plan(resource)
            resources[step.id] = resource
        return resources
