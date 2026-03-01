from pathlib import Path
from shutil import rmtree

from ..infrastructure.block import Block


class ProvisioningResource:
    def __init__(self, folder: Path) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        self._folder = folder

    @classmethod
    def from_block(cls, resources_root: Path, block: Block) -> "ProvisioningResource":
        resource_folder = resources_root / block.id
        return cls(resource_folder)

    @property
    def folder(self) -> Path:
        return self._folder

    def dump_block(self, block: Block)-> None:
        block.dump_assets(self._folder)

    def rm(self) -> None:
        if self._folder.is_dir():
            rmtree(self._folder)