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
        resources = {}
        
        for res_block in resolved_blocks:
            infra_block = blocks[res_block.id]
            resource = ProvisioningResource(resources_folder / res_block.id)
            resources[res_block.id] = resource

            print(f"Initializing Terraform for block {res_block.id}...")
            resource.dump_block(infra_block)
            self._runner.init_terraform(resource, res_block, context)

        for res_block in resolved_blocks:
            resource = resources[res_block.id]
            
            print(f"Terraform plan for block {res_block.id}:")
            self._runner.save_terraform_plan(resource)

        for res_block in resolved_blocks:
            resource = resources[res_block.id]

            print(f"Terraform apply for block {res_block.id}:")
            output = self._runner.apply_terraform(resource)
            context.set_outputs(res_block.id, res_block.contract.map_outputs(output if isinstance(output, dict) else {}))

        print("Provisioning completed successfully.")
        print("Final outputs:")
        for block_id, outputs in context._outputs.items():
            print(f"{block_id}: {outputs}")
