import os
from pathlib import Path

from ..domain.repository import BlockRepository, ResourceRepository

from .loader import FileSystemBlockLoader
from .resource import FileSystemResourceRepository


def load_block_repository() -> BlockRepository:
    """Wire a FileSystemBlockLoader from the FREELOADER_BLOCKS env variable."""
    blocks_root = os.getenv("FREELOADER_BLOCKS")
    assert blocks_root, "FREELOADER_BLOCKS environment variable must be set"
    path = Path(blocks_root)
    assert path.is_dir(), f"Blocks root does not exist: {path}"
    return FileSystemBlockLoader.init(path)


def make_resource_repository(resources_root: Path) -> ResourceRepository:
    """Wire a FileSystemResourceRepository for the given resources root directory."""
    return FileSystemResourceRepository(resources_root)
