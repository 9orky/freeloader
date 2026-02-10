from abc import ABC, abstractmethod
from typing import Any

from freeloader.pipeline.context import ExecutionContext
from freeloader.pipeline.dag import ResolvedBlock
from freeloader.shared.errors import FeasibilityIssue


class BaseRunner(ABC):
    @abstractmethod
    def runner_name(self) -> str: ...

    @abstractmethod
    def check_feasibility(
        self, blocks: list[ResolvedBlock]) -> list[FeasibilityIssue]: ...

    @abstractmethod
    def plan(self, blocks: list[ResolvedBlock],
             ctx: ExecutionContext) -> str: ...

    @abstractmethod
    def apply(self, blocks: list[ResolvedBlock],
              ctx: ExecutionContext) -> dict[str, dict[str, Any]]: ...

    @abstractmethod
    def destroy(self, blocks: list[ResolvedBlock],
                ctx: ExecutionContext) -> None: ...
