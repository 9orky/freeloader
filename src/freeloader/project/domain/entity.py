from dataclasses import dataclass

from freeloader.shared.block import BlockRef
from freeloader.shared.tech import TechStack
from freeloader.shared.types import ConfigValue


@dataclass(frozen=True)
class Manifest:
    name: str
    tech_stack: TechStack
    block_refs: tuple[BlockRef, ...]


@dataclass(frozen=True)
class CandidateBlock:
    block_id: str
    provider: str
    config: dict[str, ConfigValue]
    required_secret_keys: tuple[str, ...] = ()
    required_tech_fields: tuple[str, ...] = ()
    required_tech_stack: bool = False


__all__ = ["CandidateBlock", "Manifest", "TechStack"]
