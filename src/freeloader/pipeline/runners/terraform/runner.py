import os
import shutil
from pathlib import Path
from typing import Any

from freeloader.pipeline.blocks.registry import BlockRegistry
from freeloader.credentials.vault import SecretVault
from freeloader.pipeline.context import ExecutionContext
from freeloader.pipeline.dag import ResolvedBlock
from freeloader.pipeline.runners.base import BaseRunner
from freeloader.pipeline.runners.terraform.resource import TerraformResource
from freeloader.shared.errors import FeasibilityIssue


class TerraformRunner(BaseRunner):
    def __init__(self, resource_base_dir: Path, vault: SecretVault, block_registry: BlockRegistry) -> None:
        self._resource_base_dir = resource_base_dir
        self._vault = vault
        self._block_registry = block_registry

    def runner_name(self) -> str:
        return "terraform"

    def check_feasibility(self, block: ResolvedBlock) -> list[FeasibilityIssue]:
        issues: list[FeasibilityIssue] = []
        name = self.runner_name()

        if not shutil.which("terraform"):
            issues.append(FeasibilityIssue(
                runner=name,
                check="terraform binary",
                detail="'terraform' not found in PATH. Install: https://developer.hashicorp.com/terraform/install",
            ))

        source = self._source_tf(block)
        if not source.exists():
            issues.append(FeasibilityIssue(
                runner=name,
                check=f"tf file for '{block.contract.block.name}'",
                detail=f"No main.tf found at {source}",
            ))

        return issues

    def plan_block(self, block: ResolvedBlock, ctx: ExecutionContext) -> str:
        resource = self._build_resource(block, ctx)
        env = self._env()
        resource.init(env)
        result = resource.plan(env)
        return result.stdout

    def apply_block(self, block: ResolvedBlock, ctx: ExecutionContext) -> dict[str, Any]:
        resource = self._build_resource(block, ctx)
        env = self._env()
        timeout = block.contract.block.timeout_seconds
        resource.init(env)
        resource.apply(env, timeout=timeout)
        raw = resource.read_outputs(env)
        return self._map_outputs(block, raw)

    def destroy_block(self, block: ResolvedBlock, ctx: ExecutionContext) -> None:
        resource_dir = self._resource_dir(block)
        if not resource_dir.exists():
            return
        source = self._source_tf(block)
        resource = TerraformResource(resource_dir, source)
        variables = self._build_variables(block, ctx)
        resource.prepare(variables)
        env = self._env()
        timeout = block.contract.block.timeout_seconds
        resource.init(env)
        resource.destroy(env, timeout=timeout)

    def _build_resource(self, block: ResolvedBlock, ctx: ExecutionContext) -> TerraformResource:
        source = self._source_tf(block)
        resource = TerraformResource(self._resource_dir(block), source)
        variables = self._build_variables(block, ctx)
        resource.prepare(variables)
        return resource

    def _build_variables(self, block: ResolvedBlock, ctx: ExecutionContext) -> dict[str, Any]:
        variables: dict[str, Any] = {"name": block.ref.resolved_id}

        for key, value in block.ref.config.items():
            variables[key] = value

        for req_key, provider_id in block.inputs.items():
            var_name = req_key.replace(".", "_")
            outputs = ctx.get_all_outputs(provider_id)
            variables[var_name] = outputs.get(req_key, "")

        for secret_key in block.contract.block.required_secrets:
            var_name = secret_key.lower()
            variables[var_name] = self._vault.get(secret_key)

        return variables

    def _env(self) -> dict[str, str]:
        return dict(os.environ)

    def _source_tf(self, block: ResolvedBlock) -> Path:
        return self._block_registry.get_block_dir(block.contract.block.name) / "main.tf"

    def _resource_dir(self, block: ResolvedBlock) -> Path:
        return self._resource_base_dir / block.ref.resolved_id

    def _map_outputs(self, block: ResolvedBlock, raw: dict[str, Any]) -> dict[str, Any]:
        return block.contract.map_outputs(raw)
