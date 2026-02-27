from dataclasses import dataclass
from pathlib import Path

from ..base import BlockId
from ..resolver import BlockRef

from .block import Block


@dataclass(frozen=True)
class BlockLoader:
    folder: Path

    @classmethod
    def init(cls, path: Path) -> "BlockLoader":
        assert path.is_dir(), f"Blocks root {path} is not a directory"
        return cls(folder=path)
    
    @property
    def all_blocks(self) -> dict[str, Block]:
        blocks = {}
        for provider_folder in self.folder.iterdir():
            if not provider_folder.is_dir():
                continue
            
            for block_folder in provider_folder.iterdir():
                if not block_folder.is_dir():
                    continue
                
                block = Block.from_folder(block_folder)
                blocks[str(block.id)] = block

        return blocks

    def load_by_ids(self, block_ids: list[BlockId]) -> dict[str, Block]:
        blocks = {}
        for block_id in block_ids:
            block_folder = self.folder / block_id.sub_path
            block = Block.from_folder(block_folder)
            blocks[str(block_id)] = block

        return blocks
    
    def load_by_refs(self, block_refs: list[BlockRef]) -> dict[str, Block]:
        block_ids = [BlockId(ref.resolved_id) for ref in block_refs]
        return self.load_by_ids(block_ids)