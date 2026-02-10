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

    def check_feasibility(self, blocks: list[ResolvedBlock]) -> list[FeasibilityIssue]:
        issues: list[FeasibilityIssue] = []
        name = self.runner_name()

        for block in blocks:
            block_name = block.contract.block.name
            block_dir = self._block_dirs.get(block_name)
            if not block_dir:
                issues.append(FeasibilityIssue(
                    runner=name, check=f"block dir for '{block_name}'",
                    detail=f"No block directory registered for '{block_name}'",
                ))
                continue
            handler_path = block_dir / "handler.py"
            if not handler_path.exists():
                issues.append(FeasibilityIssue(
                    runner=name, check=f"handler for '{block_name}'",
                    detail=f"handler.py not found at {handler_path}",
                ))

        return issues

    def plan(self, blocks: list[ResolvedBlock], ctx: ExecutionContext) -> str:
        lines: list[str] = []
        for block in blocks:
            handler = self._load_handler(block)
            inputs = ctx.resolve_inputs(block.inputs)
            exists = handler.check(inputs, block.ref.config, self._secrets)
            status = "exists (update)" if exists else "create"
            lines.append(f"  [{status}] {block.ref.resolved_id}")
        return "\n".join(lines)

    def apply(self, blocks: list[ResolvedBlock], ctx: ExecutionContext) -> dict[str, dict[str, Any]]:
        all_outputs: dict[str, dict[str, Any]] = {}
        for block in blocks:
            handler = self._load_handler(block)
            inputs = ctx.resolve_inputs(block.inputs)
            outputs = handler.handle(inputs, block.ref.config, self._secrets)
            all_outputs[block.ref.resolved_id] = outputs
        return all_outputs

    def destroy(self, blocks: list[ResolvedBlock], ctx: ExecutionContext) -> None:
        for block in blocks:
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
