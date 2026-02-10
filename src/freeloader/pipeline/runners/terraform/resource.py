import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from freeloader.pipeline.runners.terraform.file import TerraformFile
from freeloader.shared import subprocess as safe_subprocess


PLAN_FILE = "tfplan"
TFVARS_FILE = "freeloader.auto.tfvars.json"


@dataclass(frozen=True)
class PlanResult:
    stdout: str
    plan_file: Path


class TerraformResource:
    def __init__(self, resource_dir: Path, source_tf: Path) -> None:
        self._dir = resource_dir
        self._source_tf = source_tf
        self._tf_file = TerraformFile(source_tf)

    @property
    def dir(self) -> Path:
        return self._dir

    @property
    def tf_file(self) -> TerraformFile:
        return self._tf_file

    def prepare(self, variables: dict[str, Any]) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self._source_tf, self._dir / "main.tf")
        (self._dir / TFVARS_FILE).write_text(json.dumps(variables, indent=2))

    def init(self, env: dict[str, str]) -> None:
        self._run(["init", "-input=false"], env)

    def plan(self, env: dict[str, str]) -> PlanResult:
        result = self._run(
            ["plan", "-input=false", f"-out={PLAN_FILE}", "-no-color"], env)
        return PlanResult(
            stdout=result.stdout,
            plan_file=self._dir / PLAN_FILE,
        )

    def apply(self, env: dict[str, str], *, timeout: int | None = None) -> None:
        plan_file = self._dir / PLAN_FILE
        args = ["apply", "-input=false"]
        if plan_file.exists():
            args.append(PLAN_FILE)
        else:
            args.append("-auto-approve")
        self._run(args, env, timeout=timeout)

    def destroy(self, env: dict[str, str], *, timeout: int | None = None) -> None:
        self._run(["destroy", "-auto-approve", "-input=false"],
                  env, timeout=timeout)

    def read_outputs(self, env: dict[str, str]) -> dict[str, Any]:
        return self.read_outputs_from_dir(self._dir, env)

    @staticmethod
    def read_outputs_from_dir(resource_dir: Path, env: dict[str, str]) -> dict[str, Any]:
        result = safe_subprocess.run(
            ["terraform", "output", "-json"],
            cwd=resource_dir,
            env=env,
            label="terraform output",
        )
        raw: dict[str, Any] = json.loads(
            result.stdout) if result.stdout.strip() else {}
        return {k: v["value"] for k, v in raw.items()}

    def _run(
        self,
        args: list[str],
        env: dict[str, str],
        timeout: int | None = None,
    ) -> safe_subprocess.subprocess.CompletedProcess[str]:
        return safe_subprocess.run(
            ["terraform", *args],
            cwd=self._dir,
            env=env,
            label=f"terraform {args[0]}",
            timeout=timeout,
        )
