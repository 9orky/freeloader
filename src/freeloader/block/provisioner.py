from pathlib import Path

from .infrastructure import BlockLoader, Block
from .context import ExecutionContext
from .resolver import BlockRef, DAGResolver
from .provision import (
    AppliedStepReport,
    DestroyReport,
    DestroyStepReport,
    ProvisioningPlan,
    ProvisioningReport,
    ProvisioningResource,
    ProvisioningStep,
)
from .runner import BlockRunner


class Provisioner:
    def __init__(
        self,
        resources_root: Path,
        loader: BlockLoader,
        runner: BlockRunner
    ) -> None:
        assert resources_root.is_dir(
        ), f"Resources root {resources_root} is not a directory"

        self._resources_root = resources_root
        self._loader = loader
        self._runner = runner
        self._resolver = DAGResolver()

    def load_resource(self, block: Block) -> ProvisioningResource:
        return ProvisioningResource.from_block(self._resources_root, block)

    def plan(self, block_refs: list[BlockRef]) -> ProvisioningPlan:
        assert block_refs, "At least one block reference must be provided"

        blocks = self._loader.load_by_refs(block_refs)
        contracts = {bid: block.contract for bid, block in blocks.items()}
        resolved_blocks = self._resolver.resolve(block_refs, contracts)

        return ProvisioningPlan(
            steps=[
                ProvisioningStep(
                    block=blocks[resolved_block.id],
                    resolved_block=resolved_block,
                )
                for resolved_block in resolved_blocks
            ]
        )

    def provision(self, block_refs: list[BlockRef]) -> ProvisioningReport:
        plan = self.plan(block_refs)
        context = ExecutionContext()
        resources = self._prepare_resources(plan)
        self._plan_resources(plan, resources)
        applied_steps: list[AppliedStepReport] = []

        for step in plan.steps:
            resource = resources[step.id]
            if step.has_inputs:
                self._runner.run_init_with_deps(
                    resource, step.resolved_block, context)
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

    def destroy(self, block_refs: list[BlockRef]) -> DestroyReport:
        plan = self.plan(block_refs)
        steps: list[DestroyStepReport] = []

        for step in reversed(plan.steps):
            resource: ProvisioningResource | None = None
            try:
                resource = self.load_resource(step.block)
                self._runner.run_destroy(resource)
                steps.append(DestroyStepReport(
                    block_id=step.id, destroyed=True))
            except Exception as e:
                steps.append(
                    DestroyStepReport(
                        block_id=step.id,
                        destroyed=False,
                        error=str(e),
                    )
                )
            finally:
                if resource is not None:
                    resource.rm()

        return DestroyReport(plan=plan, steps=steps)

    def _prepare_resources(self, plan: ProvisioningPlan) -> dict[str, ProvisioningResource]:
        resources: dict[str, ProvisioningResource] = {}
        for step in plan.steps:
            resource = self.load_resource(step.block)
            resources[step.id] = resource
            resource.dump_block(step.block)
            self._runner.run_init(resource, step.resolved_block)
        return resources

    def _plan_resources(
        self,
        plan: ProvisioningPlan,
        resources: dict[str, ProvisioningResource],
    ) -> None:
        for step in plan.steps:
            self._runner.run_plan(resources[step.id])
