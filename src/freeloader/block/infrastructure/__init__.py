import os
from pathlib import Path

from ..domain.repository import BlockRepository, SecretsReader

from .loader import FileSystemBlockLoader
from .runner import BlockRunner
from .secrets import SecretsAdapter

_PACKAGED_BLOCKS_ROOT = Path(__file__).resolve().parents[2] / "blocks"
_SOURCE_BLOCKS_ROOT = Path(__file__).resolve().parents[3] / "blocks"


def load_block_repository() -> BlockRepository:
    """Wire a FileSystemBlockLoader from src/blocks or FREELOADER_BLOCKS override."""
    blocks_root = os.getenv("FREELOADER_BLOCKS")
    path = Path(blocks_root) if blocks_root else _default_blocks_root()
    assert path.is_dir(), f"Blocks root does not exist: {path}"
    return FileSystemBlockLoader.init(path)


def _default_blocks_root() -> Path:
    if _PACKAGED_BLOCKS_ROOT.is_dir():
        return _PACKAGED_BLOCKS_ROOT
    return _SOURCE_BLOCKS_ROOT


def load_secrets_reader() -> SecretsReader:
    """Wire the default SecretsReader for block operations."""
    return SecretsAdapter()


def load_block_runner(project_root: Path) -> BlockRunner:
    """Wire the default BlockRunner for block provisioning commands."""
    return BlockRunner(project_root, load_secrets_reader())
