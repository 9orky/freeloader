from freeloader.block.domain.entity import BlockRef
from freeloader.block.domain.provisioning import ProvisioningPlan, ProvisioningStep
from freeloader.block.domain.repository import BlockRepository
from freeloader.block.domain.resolver import DAGResolver
from freeloader.block.domain.value_object import BlockId


class ProvisioningPlanBuilder:
    def __init__(
        self,
        repository: BlockRepository,
        resolver: DAGResolver | None = None,
    ) -> None:
        self._repository = repository
        self._resolver = resolver or DAGResolver()

    def build(self, block_refs: list[BlockRef]) -> ProvisioningPlan:
        assert block_refs, "At least one block reference must be provided"
        block_ids = [BlockId(ref.resolved_id) for ref in block_refs]
        blocks = self._repository.load_by_ids(block_ids)
        contracts = {block_id: block.contract for block_id,
                     block in blocks.items()}
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
