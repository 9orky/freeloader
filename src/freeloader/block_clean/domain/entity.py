from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal

from pydantic import BaseModel, computed_field

from freeloader.shared.types import ConfigValue

from . import Layer
from .value_object import BlockId

_TECH_STACK_KEYS = frozenset(
    {"language", "language_version", "package_manager", "framework"}
)

# ---------------------------------------------------------------------------
# Contract types (ported from block/contract.py)
# ---------------------------------------------------------------------------


class CostTier(str, Enum):
    always_free = "always_free"
    free_tier = "free_tier"
    paid = "paid"


class FreeTierLimit(BaseModel):
    metric: str
    amount: float
    period: str


class BlockCostSpec(BaseModel):
    tier: CostTier = CostTier.paid
    free_tier_limits: list[FreeTierLimit] = []
    estimated_monthly_usd: str = ""
    note: str = ""


class BlockMeta(BaseModel):
    description: str = ""
    layer: Layer
    required_tech_stack: bool = False


class ConfigField(BaseModel):
    name: str
    description: str = ""
    required: bool = False
    default: ConfigValue | None = None
    choices: list[str] | None = None
    group: Literal["basic", "advanced", "secrets"] = "basic"
    project_name_default: bool = False


class PortSpec(BaseModel):
    description: str = ""
    optional: bool = False
    sensitive: bool = False


class BlockContract(BaseModel):
    block: BlockMeta
    provides: dict[str, PortSpec] = {}
    requires: dict[str, PortSpec] = {}
    config: list[ConfigField] = []
    costs: BlockCostSpec = BlockCostSpec()

    @property
    def required_secret_keys(self) -> list[str]:
        return [f.name for f in self.config if f.group == "secrets"]

    def config_fields(self, group: str) -> list[ConfigField]:
        return [f for f in self.config if f.group == group]


# ---------------------------------------------------------------------------
# Block domain entity (new — path-free representation of a block definition)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Block:
    id: BlockId
    contract: BlockContract


# ---------------------------------------------------------------------------
# Execution context types (ported from block/context.py)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class OutputReference:
    requirement_key: str
    provider_id: str
    output_name: str

    @classmethod
    def from_input(cls, requirement_key: str, provider_id: str) -> "OutputReference":
        _, output_name = requirement_key.split(".", 1)
        return cls(
            requirement_key=requirement_key,
            provider_id=provider_id,
            output_name=output_name,
        )


# ---------------------------------------------------------------------------
# Resolver reference types (ported from block/resolver/base.py)
# ---------------------------------------------------------------------------


class BlockRef(BaseModel):
    use: str
    id: str | None = None
    config: dict[str, ConfigValue | None] = {}

    @computed_field
    @property
    def resolved_id(self) -> str:
        return self.id or self.use


@dataclass(frozen=True)
class ResolvedBlock:
    ref: BlockRef
    contract: BlockContract
    inputs: list["OutputReference"]

    @property
    def id(self) -> str:
        return self.ref.resolved_id
