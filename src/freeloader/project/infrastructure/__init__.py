from __future__ import annotations

from ..domain.repository import BlockGateway, ManifestRepository, TechStackDetector
from .manifest_store import YamlManifestStore
from .tech_stack import TechFacadeDetector
from .block_gateway import BlockSystemGateway


def load_manifest_repository() -> ManifestRepository:
    return YamlManifestStore()


def load_tech_stack_detector() -> TechStackDetector:
    return TechFacadeDetector()


def load_block_gateway() -> BlockGateway:
    return BlockSystemGateway()


__all__ = [
    "load_manifest_repository",
    "load_tech_stack_detector",
    "load_block_gateway",
]
