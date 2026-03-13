from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RuleViolation:
    message: str
    file_path: Path | None = None
    line: int | None = None


@dataclass(frozen=True)
class RuleResult:
    rule_id: str
    title: str
    description: str
    violations: list[RuleViolation]

    @property
    def passed(self) -> bool:
        return not self.violations


@dataclass(frozen=True)
class PipelineResult:
    results: list[RuleResult]

    @property
    def failed(self) -> bool:
        return any(not result.passed for result in self.results)
