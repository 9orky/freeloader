from __future__ import annotations

import dataclasses

from freeloader.block import BlockRef


@dataclasses.dataclass(frozen=True)
class TechStack:
    language: str | None = None
    language_version: str | None = None
    package_manager: str | None = None
    framework: str | None = None


@dataclasses.dataclass(frozen=True)
class Manifest:
    name: str
    tech_stack: TechStack
    block_refs: tuple[BlockRef, ...]
