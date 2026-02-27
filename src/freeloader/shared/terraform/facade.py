from dataclasses import dataclass
import json
from typing import Union
from pathlib import Path

from .runner import TerraformRunner

MAIN_FILE = "main.tf"
PLAN_FILE = "tfplan"
TFVARS_FILE = "freeloader.auto.tfvars.json"


@dataclass(frozen=True)
class TerraformPlan:
    stdout: str
    plan_file: Path


class TerraformResource:
    def __init__(self, root: Path) -> None:
        root.mkdir(parents=True, exist_ok=True)
        self._root = root
        self._runner = TerraformRunner(root)

    def init(self, variables: dict[str, str | list | dict]) -> None:
        self._create_variables_file(variables)
        self._runner.init()

    def plan(self) -> str:
        return self._runner.plan(PLAN_FILE)

    def apply(self, *, timeout: int | None = None) -> None:
        self._must_be_prepared()
        self._runner.apply(PLAN_FILE, timeout=timeout)

    def output(self) -> Union[dict, list]:
        self._must_be_created()
        return self._runner.output()

    def destroy(self, *, timeout: int | None = None) -> None:
        self._must_be_created()
        self._runner.destroy(timeout=timeout)

    def _create_variables_file(self, variables: dict[str, str | list | dict]) -> None:
        variables_file = self._root / TFVARS_FILE
        variables_file.write_text(json.dumps(variables, indent=2))

    def _must_be_prepared(self) -> None:
        main_file = self._root / MAIN_FILE
        plan_file = self._root / PLAN_FILE
        assert main_file.is_file(), f"Terraform main file not found: {main_file}"
        assert plan_file.is_file(), f"Terraform plan file not found: {plan_file}"

    def _must_be_created(self) -> None:
        main_file = self._root / MAIN_FILE
        plan_file = self._root / PLAN_FILE
        assert main_file.is_file(), f"Terraform main file not found: {main_file}"
        assert plan_file.is_file(), f"Terraform plan file should be removed after apply: {plan_file}"
