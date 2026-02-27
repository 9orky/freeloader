from pathlib import Path

from freeloader.shared.terraform import TerraformResource

from ..base import SecretsReader
from ..context import ExecutionContext
from ..resolver import ResolvedBlock
from ..provision import ProvisioningResource

from .variables import VariablesBuilder


class BlockRunner:
    def __init__(self, project_path: Path, secrets: SecretsReader) -> None:
        self._variables_builder = VariablesBuilder(project_path, secrets)

    def init_terraform(self, resource: ProvisioningResource, block: ResolvedBlock, context: ExecutionContext) -> None:
        tfvars = self._variables_builder.build(block, context)
        TerraformResource(resource.folder).init(tfvars)

    def save_terraform_plan(self, resource: ProvisioningResource) -> None:
        TerraformResource(resource.folder).plan()

    def apply_terraform(self, resource: ProvisioningResource) -> None:
        pass

        # self._terraform.apply()
        # raw = self._terraform.output()

        # outputs = block.contract.map_outputs(raw if isinstance(raw, dict) else {})
        # context.set_outputs(block.id, outputs)
