from pathlib import Path
from typing import Union

from .file import TerraformFile
from .resource import TerraformResource
from .variable import TerraformVariable


class Terraform:
    def __init__(self, root: Path) -> None:
        self._resource = TerraformResource(root)

    def variables(self, template: Path) -> list[TerraformVariable]:
        return TerraformFile(template).variables

    def prepare(self, template: Path, variables: dict[str, str | list | dict]) -> None:
        self._resource.prepare(TerraformFile(template), variables)

    def apply(self, *, timeout: int | None = None) -> None:
        self._resource.apply(timeout=timeout)

    def output(self) -> Union[dict, list]:
        return self._resource.output()

    def destroy(self, *, timeout: int | None = None) -> None:
        self._resource.destroy(timeout=timeout)
