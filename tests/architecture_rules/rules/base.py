from __future__ import annotations

from abc import ABC, abstractmethod

from ..context import ArchitectureContext
from ..results import RuleResult, RuleViolation


class ArchitectureRule(ABC):
    rule_id: str
    title: str
    description: str

    def check(self, context: ArchitectureContext) -> RuleResult:
        return RuleResult(
            rule_id=self.rule_id,
            title=self.title,
            description=self.description,
            violations=self.violations(context),
        )

    @abstractmethod
    def violations(
        self, context: ArchitectureContext) -> list[RuleViolation]: ...

    def violation(self, message: str) -> RuleViolation:
        return RuleViolation(message=message)
