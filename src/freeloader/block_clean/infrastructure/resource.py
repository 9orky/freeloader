from pathlib import Path
from shutil import rmtree

from ..domain.entity import ProvisionedResource
from ..domain.repository import ResourceRepository
from ..domain.value_object import BlockId

from .block import SourceBlock


class ProvisioningResource:
    """Ephemeral Terraform workspace directory for one block during provisioning."""

    def __init__(self, folder: Path) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        self._folder = folder

    @property
    def folder(self) -> Path:
        return self._folder

    def dump_block(self, source_block: SourceBlock) -> None:
        source_block.dump_assets(self._folder)

    def rm(self) -> None:
        if self._folder.is_dir():
            rmtree(self._folder)


class FileSystemResourceRepository(ResourceRepository):
    """Persisted Terraform workspace directory collection on disk.

    Each workspace folder is named by the string form of its `BlockId`
    (e.g. ``github.remote_repo``), kept flat under `resources_root`.
    This is separate from the nested ``sub_path`` layout of the blocks source tree.
    """

    def __init__(self, resources_root: Path) -> None:
        resources_root.mkdir(parents=True, exist_ok=True)
        self._root = resources_root

    def create(self, block_id: BlockId) -> ProvisionedResource:
        (self._root / str(block_id)).mkdir(parents=True, exist_ok=True)
        return ProvisionedResource(block_id=block_id)

    def get(self, block_id: BlockId) -> ProvisionedResource | None:
        if (self._root / str(block_id)).is_dir():
            return ProvisionedResource(block_id=block_id)
        return None

    def remove(self, block_id: BlockId) -> None:
        folder = self._root / str(block_id)
        if folder.is_dir():
            rmtree(folder)

    def list_all(self) -> list[ProvisionedResource]:
        result: list[ProvisionedResource] = []
        for p in self._root.iterdir():
            if not p.is_dir():
                continue
            try:
                result.append(ProvisionedResource(block_id=BlockId(p.name)))
            except ValueError:
                pass  # skip non-block directories (e.g. .DS_Store)
        return result
