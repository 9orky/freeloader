from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias

from freeloader.shared.types import ConfigValue

from .provisioning import DestroyReport, ProvisioningReport


ProvisionPhase = Literal["prepare", "dependency_inputs", "apply"]


@dataclass(frozen=True)
class ProvisioningStarted:
    total_blocks: int
    block_ids: list[str]


@dataclass(frozen=True)
class BlockPreparationStarted:
    block_id: str
    index: int
    total: int


@dataclass(frozen=True)
class BlockPreparationCompleted:
    block_id: str
    index: int
    total: int


@dataclass(frozen=True)
class BlockApplyStarted:
    block_id: str
    index: int
    total: int
    has_dependency_inputs: bool


@dataclass(frozen=True)
class BlockDependencyInputsStarted:
    block_id: str
    index: int
    total: int
    provider_ids: list[str]


@dataclass(frozen=True)
class BlockApplyCompleted:
    block_id: str
    index: int
    total: int
    outputs: dict[str, ConfigValue | None]


@dataclass(frozen=True)
class ProvisioningFailed:
    block_id: str
    phase: ProvisionPhase
    error: str


@dataclass(frozen=True)
class ProvisioningFinished:
    report: ProvisioningReport


@dataclass(frozen=True)
class DestroyStarted:
    total_blocks: int
    block_ids: list[str]


@dataclass(frozen=True)
class BlockDestroyStarted:
    block_id: str
    index: int
    total: int


@dataclass(frozen=True)
class BlockDestroyCompleted:
    block_id: str
    index: int
    total: int


@dataclass(frozen=True)
class BlockDestroyFailed:
    block_id: str
    index: int
    total: int
    error: str


@dataclass(frozen=True)
class DestroyFinished:
    report: DestroyReport


BlockProvisionEvent: TypeAlias = (
    ProvisioningStarted
    | BlockPreparationStarted
    | BlockPreparationCompleted
    | BlockApplyStarted
    | BlockDependencyInputsStarted
    | BlockApplyCompleted
    | ProvisioningFailed
    | ProvisioningFinished
)


BlockDestroyEvent: TypeAlias = (
    DestroyStarted
    | BlockDestroyStarted
    | BlockDestroyCompleted
    | BlockDestroyFailed
    | DestroyFinished
)


__all__ = [
    "BlockApplyCompleted",
    "BlockApplyStarted",
    "BlockDependencyInputsStarted",
    "BlockDestroyCompleted",
    "BlockDestroyEvent",
    "BlockDestroyFailed",
    "BlockDestroyStarted",
    "BlockPreparationCompleted",
    "BlockPreparationStarted",
    "BlockProvisionEvent",
    "DestroyFinished",
    "DestroyStarted",
    "ProvisionPhase",
    "ProvisioningFailed",
    "ProvisioningFinished",
    "ProvisioningStarted",
]
