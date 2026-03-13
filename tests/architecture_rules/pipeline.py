from __future__ import annotations

from dataclasses import dataclass

from .context import ArchitectureContext
from .results import PipelineResult
from .rules.base import ArchitectureRule


@dataclass(frozen=True)
class RulePipeline:
    rules: tuple[ArchitectureRule, ...]

    def run(self, context: ArchitectureContext) -> PipelineResult:
        return PipelineResult([rule.check(context) for rule in self.rules])
