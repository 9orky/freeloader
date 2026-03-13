from dataclasses import dataclass

from freeloader.shared.block import BlockRef
from freeloader.shared.tech import TechStack


@dataclass(frozen=True)
class Manifest:
    name: str
    tech_stack: TechStack
    block_refs: tuple[BlockRef, ...]


__all__ = ["Manifest", "TechStack"]
