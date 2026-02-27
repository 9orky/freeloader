from pathlib import Path
from typing import Any
import json

from ..infrastructure.block import Block


class ProvisioningResource:
    def __init__(self, folder: Path) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        self._folder = folder

    @property
    def folder(self) -> Path:
        return self._folder

    def dump_block(self, block: Block)-> None:
        block.dump_assets(self._folder)

    # def dump_terraform_file(self, terraform_template: Path) -> None:
    #     terraform_template_dest = self._folder / "main.tf"
    #     terraform_template_dest.write_text(terraform_template.read_text())

    def dump_variables(self, variables: dict[str, Any]) -> None:
        variables_dest = self._folder / "variables.tfvars.json"
        tf_vars = json.dumps(variables, indent=2)
        variables_dest.write_text(tf_vars)