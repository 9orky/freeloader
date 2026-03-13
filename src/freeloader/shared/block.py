from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias

from pydantic import BaseModel, computed_field

from .types import ConfigValue


ProvisionPhase = Literal["prepare", "dependency_inputs", "apply"]


class BlockRef(BaseModel):
    use: str
    id: str | None = None
    config: dict[str, ConfigValue | None] = {}

    @computed_field
    @property
    def resolved_id(self) -> str:
        return self.id or self.use


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
    report: object


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
    report: object


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
    "BlockRef",
    "DestroyFinished",
    "DestroyStarted",
    "ProvisionPhase",
    "ProvisioningFailed",
    "ProvisioningFinished",
    "ProvisioningStarted",
]
