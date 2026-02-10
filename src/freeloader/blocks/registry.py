from pathlib import Path

from freeloader.blocks.models import BlockContract
from freeloader.shared.paths import blocks_dir, bundled_blocks_dir
from freeloader.shared.yaml_io import load_yaml_model


class BlockRegistry:
    def __init__(self, user_dir: Path | None = None, bundled_dir: Path | None = None) -> None:
        self._user_dir = user_dir or blocks_dir()
        self._bundled_dir = bundled_dir or bundled_blocks_dir()
        self._cache: dict[str, tuple[BlockContract, Path]] = {}

    def _scan(self) -> None:
        self._cache.clear()
        for source_dir in (self._bundled_dir, self._user_dir):
            if not source_dir.exists():
                continue
            for block_yaml in sorted(source_dir.glob("*/block.yaml")):
                contract = load_yaml_model(block_yaml, BlockContract)
                self._cache[contract.block.name] = (
                    contract, block_yaml.parent)

    def _ensure_loaded(self) -> None:
        if not self._cache:
            self._scan()

    def list_blocks(self, layer: str | None = None) -> list[BlockContract]:
        self._ensure_loaded()
        contracts = [c for c, _ in self._cache.values()]
        if layer:
            contracts = [c for c in contracts if c.block.layer.value == layer]
        return contracts

    def get_block(self, name: str) -> BlockContract:
        self._ensure_loaded()
        return self._cache[name][0]

    def get_block_dir(self, name: str) -> Path:
        self._ensure_loaded()
        return self._cache[name][1]

    def has_block(self, name: str) -> bool:
        self._ensure_loaded()
        return name in self._cache

    def reload(self) -> None:
        self._scan()
