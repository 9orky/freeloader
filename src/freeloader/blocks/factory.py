from freeloader.blocks.registry import BlockRegistry
from freeloader.blocks.usecases import BlockUseCases
from freeloader.shared.paths import blocks_dir, bundled_blocks_dir


class BlocksFactory:
    def __init__(self) -> None:
        self._registry = BlockRegistry(blocks_dir(), bundled_blocks_dir())

    @property
    def registry(self) -> BlockRegistry:
        return self._registry

    def usecases(self) -> BlockUseCases:
        return BlockUseCases(self._registry)
