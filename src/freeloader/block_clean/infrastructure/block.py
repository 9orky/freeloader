import shutil
from dataclasses import dataclass
from pathlib import Path

from ..domain.entity import Block


@dataclass(frozen=True)
class SourceBlock:
    block: Block
    source_folder: Path

    def dump_assets(self, target: Path) -> None:
        """Copy Terraform source files from the block's folder into `target`."""
        shutil.copytree(self.source_folder, target, dirs_exist_ok=True)
