import importlib.util
from pathlib import Path
from typing import Any

from freeloader.pipeline.context import ExecutionContext
from freeloader.pipeline.dag import ResolvedBlock
from freeloader.pipeline.runners.base import BaseRunner
from freeloader.shared.errors import FeasibilityIssue


class APIRunner(BaseRunner):
    def __init__(self, block_dirs: dict[str, Path], secrets: dict[str, str]) -> None:
        self._block_dirs = block_dirs
        self._secrets = secrets

    def runner_name(self) -> str:
        return "api"

    def check_feasibility(self, block: ResolvedBlock) -> list[FeasibilityIssue]:
        block_dir, issues = self._check_block_dir(self._block_dirs, block)
        if issues:
            return issues
        handler_path = block_dir / "handler.py"
        if not handler_path.exists():
            issues.append(FeasibilityIssue(
                runner=self.runner_name(), check=f"handler for '{block.contract.block.name}'",
                detail=f"handler.py not found at {handler_path}",
            ))
        return issues

    def plan_block(self, block: ResolvedBlock, ctx: ExecutionContext) -> str:
        handler = self._load_handler(block)
        inputs = ctx.resolve_inputs(block.inputs)
        exists = handler.check(inputs, block.ref.config, self._secrets)
        status = "exists (update)" if exists else "create"
        return f"  [{status}] {block.ref.resolved_id}"

    def apply_block(self, block: ResolvedBlock, ctx: ExecutionContext) -> dict[str, Any]:
        handler = self._load_handler(block)
        inputs = ctx.resolve_inputs(block.inputs)
        return handler.handle(inputs, block.ref.config, self._secrets)

    def destroy_block(self, block: ResolvedBlock, ctx: ExecutionContext) -> None:
        handler = self._load_handler(block)
        inputs = ctx.resolve_inputs(block.inputs)
        state = ctx.get_all_outputs(block.ref.resolved_id)
        handler.destroy(inputs, block.ref.config, self._secrets, state)

    def _load_handler(self, block: ResolvedBlock) -> Any:
        block_name = block.contract.block.name
        handler_path = self._block_dirs[block_name] / "handler.py"
        spec = importlib.util.spec_from_file_location(
            f"freeloader.handlers.{block_name}", handler_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
