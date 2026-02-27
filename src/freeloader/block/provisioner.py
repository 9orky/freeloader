from pathlib import Path

from .infrastructure import BlockLoader
from .context import ExecutionContext
from .resolver import BlockRef, DAGResolver
from .runner import BlockRunner
from .provision import ProvisioningResource


class Provisioner:
    def __init__(self, loader: BlockLoader, runner: BlockRunner) -> None:
        self._loader = loader
        self._runner = runner
        self._resolver = DAGResolver()

    def provision(self, resources_folder: Path,  block_refs: list[BlockRef]) -> None:
        assert resources_folder.is_dir(), f"Folder {resources_folder} not found"
        assert block_refs, "At least one block reference must be provided"
        
        blocks = self._loader.load_by_refs(block_refs)
        contracts = {bid: block.contract for bid, block in blocks.items()}
        resolved_blocks = self._resolver.resolve(block_refs, contracts)

        context = ExecutionContext()

        for res_block in resolved_blocks:
            infra_block = blocks[res_block.id]
            resource = ProvisioningResource(resources_folder / res_block.id)
            resource.dump_terraform_file(infra_block.terraform_file)
            self._runner.run_one(resource, res_block, context)