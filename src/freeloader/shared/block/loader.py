from pathlib import Path

import yaml

from .checkers import validate_blocks_root
from .config import BlockContract


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text()) or {}


class BlockLoader:
    def __init__(self, blocks_root: Path) -> None:
        validate_blocks_root(blocks_root)
        self._root = blocks_root

    def load_all(self) -> dict[str, BlockContract]:
        result: dict[str, BlockContract] = {}
        for block_yml in self._root.rglob("block.yml"):
            relative = block_yml.parent.relative_to(self._root)
            block_id = str(relative)
            result[block_id] = self._parse(block_yml)
        return result

    def load(self, block_id: str) -> BlockContract:
        path = self._root / block_id / "block.yml"
        return self._parse(path)

    def _parse(self, path: Path) -> BlockContract:
        data = _load_yaml(path)
        return BlockContract.model_validate(data)

    def block_ids(self) -> list[str]:
        return [
            str(p.parent.relative_to(self._root))
            for p in self._root.rglob("block.yml")
        ]
