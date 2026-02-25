from pathlib import Path

from .base import Block, BlockId, BlockRepository
from .contract import BlockContract
from .dag import BlockRef, DAGResolver, ResolvedBlock


class Provisioner:
    def __init__(self, folder: Path, block_repository: BlockRepository) -> None:
        assert folder.is_dir(), f"Folder {folder} does not exist or is not a directory"

        self._repository = block_repository
        self._resolver = DAGResolver()
        self._folder = folder

    def provision(self, block_refs: list[BlockRef]):
        if not block_refs:
            raise ValueError("No Blocks to provision")
        
        blocks_ids = [BlockId(ref.resolved_id) for ref in block_refs]

        blocks = {
            block_id: self._repository.get_by_id(block_id) 
            for block_id in blocks_ids
        }
        
        contracts = {
            str(block.id): BlockContract.model_validate(block.contract) 
            for block in blocks.values()
        }
        
        resolved_blocks = self._resolver.resolve(block_refs, contracts)


