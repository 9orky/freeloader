from __future__ import annotations

from dataclasses import dataclass

from freeloader.shared.types import ConfigValue

from ....domain.entity import Block, ResolvedBlock


@dataclass(frozen=True)
class ProvisioningStep:
    block: Block
    resolved_block: ResolvedBlock

    @property
    def id(self) -> str:
        return self.resolved_block.id

    @property
    def has_inputs(self) -> bool:
        return bool(self.resolved_block.inputs)


@dataclass(frozen=True)
class ProvisioningPlan:
    steps: list[ProvisioningStep]

    @property
    def block_ids(self) -> list[str]:
        return [step.id for step in self.steps]


@dataclass(frozen=True)
class AppliedStepReport:
    block_id: str
    outputs: dict[str, ConfigValue | None]
    had_dependency_inputs: bool


@dataclass(frozen=True)
class ProvisioningReport:
    plan: ProvisioningPlan
    applied_steps: list[AppliedStepReport]

    @property
    def outputs_by_block(self) -> dict[str, dict[str, ConfigValue | None]]:
        return {step.block_id: dict(step.outputs) for step in self.applied_steps}


@dataclass(frozen=True)
class DestroyStepReport:
    block_id: str
    destroyed: bool
    error: str = ""


@dataclass(frozen=True)
class DestroyReport:
    plan: ProvisioningPlan
    steps: list[DestroyStepReport]

    @property
    def destroyed_block_ids(self) -> list[str]:
        return [step.block_id for step in self.steps if step.destroyed]

    @property
    def failed_block_ids(self) -> list[str]:
        return [step.block_id for step in self.steps if not step.destroyed]
