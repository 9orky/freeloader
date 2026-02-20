import json
from pathlib import Path
from subprocess import run, CalledProcessError
from typing import Union


class TerraformRunner:
    def __init__(self, root: Path) -> None:
        self._root = root

    def init(self) -> None:
        self._run(["terraform", "init", "-input=false"])

    def plan(self, plan_file: str) -> str:
        return self._run(["terraform", "plan", "-input=false", "-no-color", f"-out={plan_file}"])

    def apply(self, plan_file: str, timeout: int | None = None) -> None:
        self._run(["terraform", "apply", "-input=false", plan_file])

    def output(self) -> Union[dict, list]:
        raw = self._run(["terraform", "output", "-json"])
        return json.loads(raw) if raw.strip() else {}

    def destroy(self, timeout: int | None = None) -> None:
        self._run(["terraform", "destroy", "-auto-approve", "-input=false"])

    def _run(self, command: list[str]) -> str:
        try:
            result = run(command, capture_output=True,
                         text=True, check=True, cwd=self._root)
            return result.stdout
        except CalledProcessError as e:
            raise RuntimeError(
                f"Terraform command failed: {' '.join(command)}\n{e.stderr}"
            ) from e
