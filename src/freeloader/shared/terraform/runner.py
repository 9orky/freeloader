from pathlib import Path
from typing import Union

from freeloader.shared.cmd import run_cli


class TerraformRunner:
    def __init__(self, root: Path) -> None:
        self._root = root

    def init(self) -> None:
        run_cli(["terraform", "init", "-input=false"], chdir=self._root)

    def plan(self, plan_file: str) -> str:
        result = run_cli(["terraform", "plan", "-input=false", "-no-color", f"-out={plan_file}"], chdir=self._root)
        return result.raw

    def apply(self, plan_file: str, timeout: int | None = None) -> None:
        run_cli(["terraform", "apply", "-input=false", plan_file], chdir=self._root)

    def output(self) -> Union[dict, list]:
        result = run_cli(["terraform", "output", "-json"], chdir=self._root)
        return result.json

    def destroy(self, timeout: int | None = None) -> None:
        run_cli(["terraform", "destroy", "-auto-approve", "-input=false"], chdir=self._root)