from pathlib import Path

from .infrastructure import BlockLoader, Block
from .context import ExecutionContext
from .resolver import BlockRef, DAGResolver
from .runner import BlockRunner
from .provision import ProvisioningResource


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

    def provision(self, block_refs: list[BlockRef]) -> None:
        assert block_refs, "At least one block reference must be provided"

        blocks = self._loader.load_by_refs(block_refs)
        contracts = {bid: block.contract for bid, block in blocks.items()}
        resolved_blocks = self._resolver.resolve(block_refs, contracts)

        context = ExecutionContext()
        resources: dict[str, ProvisioningResource] = {}

        for res_block in resolved_blocks:
            block = blocks[res_block.id]
            resource = self.load_resource(block)
            resources[res_block.id] = resource

            print(f"Block dump of {res_block.id}...")
            resource.dump_block(block)

            print(f"Init of {res_block.id}...")
            self._runner.run_init(resource, res_block)

        for res_block in resolved_blocks:
            print(f"Plan for {res_block.id}...")
            self._runner.run_plan(resources[res_block.id])

        for res_block in resolved_blocks:
            resource = resources[res_block.id]
            if res_block.inputs:
                self._runner.run_init_with_deps(resource, res_block, context)
                self._runner.run_plan(resource)
            
            output = self._runner.run_apply(resource)
            context.set_outputs(res_block.id, output)

    def destroy(self, block_refs: list[BlockRef]) -> None:
        assert block_refs, "At least one block reference must be provided"

        blocks = self._loader.load_by_refs(block_refs)
        contracts = {bid: block.contract for bid, block in blocks.items()}
        resolved_blocks = self._resolver.resolve(block_refs, contracts)

        for res_block in reversed(resolved_blocks):
            try:
                block = blocks[res_block.id]
                resource = self.load_resource(block)
            except Exception as e:
                print(f"Failed to load resource for block {res_block.id}: {e}")
                continue
            
            try:
                print(f"Destroying resources for block {res_block.id}...")
                self._runner.run_destroy(resource)
            except Exception as e:
                print(f"Failed to destroy resources for block {res_block.id}: {e}")

            resource.rm()
