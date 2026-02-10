from dataclasses import dataclass

from freeloader.pipeline.blocks.models import BlockContract
from freeloader.pipeline.blocks.registry import BlockRegistry


@dataclass(frozen=True)
class BlockInfo:
    name: str
    layer: str
    runner: str
    provides: list[str]
    requires: list[str]


@dataclass(frozen=True)
class ListBlocksResult:
    blocks: list[BlockInfo]


class BlockUseCases:
    def __init__(self, registry: BlockRegistry) -> None:
        self._registry = registry

    def list(self, layer: str | None = None) -> ListBlocksResult:
        contracts = self._registry.list_blocks()
        if layer:
            contracts = [c for c in contracts if c.block.layer.value == layer]
        blocks = [
            BlockInfo(
                name=c.block.name,
                layer=c.block.layer.value,
                runner=c.block.runner.value,
                provides=sorted(c.provides.keys()),
                requires=sorted(c.requires.keys()),
            )
            for c in sorted(contracts, key=lambda x: x.block.layer.value)
        ]
        return ListBlocksResult(blocks=blocks)
