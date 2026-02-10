from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from freeloader.pipeline.context import ExecutionContext
from freeloader.pipeline.dag import ResolvedBlock
from freeloader.shared.errors import FeasibilityIssue


class BaseRunner(ABC):
    @abstractmethod
    def runner_name(self) -> str: ...

    @abstractmethod
    def check_feasibility(
        self, block: ResolvedBlock) -> list[FeasibilityIssue]: ...

    @abstractmethod
    def plan_block(self, block: ResolvedBlock,
                   ctx: ExecutionContext) -> str: ...

    @abstractmethod
    def apply_block(self, block: ResolvedBlock,
                    ctx: ExecutionContext) -> dict[str, Any]: ...

    @abstractmethod
    def destroy_block(self, block: ResolvedBlock,
                      ctx: ExecutionContext) -> None: ...

    def _check_block_dir(
        self, block_dirs: dict[str, Path], block: ResolvedBlock,
    ) -> tuple[Path | None, list[FeasibilityIssue]]:
        block_name = block.contract.block.name
        block_dir = block_dirs.get(block_name)
        if not block_dir:
            return None, [FeasibilityIssue(
                runner=self.runner_name(),
                check=f"block dir for '{block_name}'",
                detail=f"No block directory registered for '{block_name}'",
            )]
        return block_dir, []
