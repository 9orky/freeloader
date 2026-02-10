import json
import os
import shutil
from pathlib import Path
from typing import Any

from freeloader.pipeline.context import ExecutionContext
from freeloader.pipeline.dag import ResolvedBlock
from freeloader.pipeline.runners.base import BaseRunner
from freeloader.credentials.vault import SecretVault
from freeloader.shared.errors import FeasibilityIssue
from freeloader.shared import subprocess as safe_subprocess


class TerraformRunner(BaseRunner):
    def __init__(self, tf_base_dir: Path, vault: SecretVault, block_dirs: dict[str, Path]) -> None:
        self._tf_base_dir = tf_base_dir
        self._vault = vault
        self._block_dirs = block_dirs

    def runner_name(self) -> str:
        return "terraform"

    def check_feasibility(self, blocks: list[ResolvedBlock]) -> list[FeasibilityIssue]:
        issues: list[FeasibilityIssue] = []
        name = self.runner_name()

        if not shutil.which("terraform"):
            issues.append(FeasibilityIssue(
                runner=name,
                check="terraform binary",
                detail="'terraform' not found in PATH. Install: https://developer.hashicorp.com/terraform/install",
            ))

        for block in blocks:
            block_name = block.contract.block.name
            if block_name not in self._block_dirs:
                issues.append(FeasibilityIssue(
                    runner=name, check=f"block dir for '{block_name}'",
                    detail=f"No block directory registered for '{block_name}'",
                ))
                continue
            source = self._block_dirs[block_name]
            if not list(source.glob("*.tf")):
                issues.append(FeasibilityIssue(
                    runner=name, check=f"tf files for '{block_name}'",
                    detail=f"No .tf files found in {source}",
                ))

        return issues

    def plan(self, blocks: list[ResolvedBlock], ctx: ExecutionContext) -> str:
        sections: list[str] = []
        for block in blocks:
            work_dir = self._prepare_workspace(block, ctx)
            env = self._build_env(block)
            self._run_tf(["init", "-input=false"], work_dir, env)
            result = self._run_tf(
                ["plan", "-no-color", "-input=false"], work_dir, env)
            sections.append(f"── {block.ref.resolved_id} ──\n{result.stdout}")
        return "\n".join(sections)

    def apply(self, blocks: list[ResolvedBlock], ctx: ExecutionContext) -> dict[str, dict[str, Any]]:
        all_outputs: dict[str, dict[str, Any]] = {}
        for block in blocks:
            work_dir = self._prepare_workspace(block, ctx)
            env = self._build_env(block)
            self._run_tf(["init", "-input=false"], work_dir, env)
            self._run_tf(["apply", "-auto-approve",
                         "-input=false"], work_dir, env)
            outputs = self._parse_outputs(block, work_dir, env)
            all_outputs[block.ref.resolved_id] = outputs
            ctx.set_outputs(block.ref.resolved_id, outputs)
        return all_outputs

    def destroy(self, blocks: list[ResolvedBlock], ctx: ExecutionContext) -> None:
        for block in reversed(blocks):
            work_dir = self._work_dir(block)
            if not work_dir.exists():
                continue
            env = self._build_env(block)
            self._run_tf(["init", "-input=false"], work_dir, env)
            self._run_tf(
                ["destroy", "-auto-approve", "-input=false"],
                work_dir, env, timeout=30,
            )

    def _work_dir(self, block: ResolvedBlock) -> Path:
        return self._tf_base_dir / block.ref.resolved_id

    def _prepare_workspace(self, block: ResolvedBlock, ctx: ExecutionContext) -> Path:
        work_dir = self._work_dir(block)
        work_dir.mkdir(parents=True, exist_ok=True)

        source = self._block_dirs[block.contract.block.name]
        for tf_file in source.glob("*.tf"):
            shutil.copy2(tf_file, work_dir / tf_file.name)

        tfvars = self._build_tfvars(block, ctx)
        (work_dir / "terraform.tfvars.json").write_text(json.dumps(tfvars, indent=2))

        return work_dir

    def _build_tfvars(self, block: ResolvedBlock, ctx: ExecutionContext) -> dict[str, Any]:
        tfvars: dict[str, Any] = {}

        for cfg_key, cfg_val in block.ref.config.items():
            tfvars[cfg_key] = cfg_val

        for req_key, provider_id in block.inputs.items():
            var_name = req_key.replace(".", "_")
            outputs = ctx.get_all_outputs(provider_id)
            tfvars[var_name] = outputs.get(req_key, f"pending-{req_key}")

        return tfvars

    def _build_env(self, block: ResolvedBlock) -> dict[str, str]:
        env = dict(os.environ)
        for secret_key in block.contract.block.required_secrets:
            if self._vault.has(secret_key):
                env[secret_key] = self._vault.get(secret_key)
        return env

    def _run_tf(
        self, args: list[str], work_dir: Path, env: dict[str, str],
        timeout: int | None = None,
    ) -> "safe_subprocess.subprocess.CompletedProcess[str]":
        return safe_subprocess.run(
            ["terraform", *args],
            cwd=work_dir,
            env=env,
            label=f"terraform {args[0]}",
            timeout=timeout,
        )

    def _parse_outputs(
        self, block: ResolvedBlock, work_dir: Path, env: dict[str, str],
    ) -> dict[str, Any]:
        result = self._run_tf(["output", "-json"], work_dir, env)
        tf_outputs: dict[str, Any] = json.loads(
            result.stdout) if result.stdout.strip() else {}

        outputs: dict[str, Any] = {}
        for port_key in block.contract.provides:
            tf_attr = port_key.split(".")[-1]
            if tf_attr in tf_outputs:
                outputs[port_key] = tf_outputs[tf_attr]["value"]
        return outputs
