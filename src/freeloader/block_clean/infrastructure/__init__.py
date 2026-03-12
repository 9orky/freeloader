import os
from pathlib import Path

from ..domain.repository import BlockRepository, SecretsReader

from .loader import FileSystemBlockLoader
from .secrets import SecretsAdapter

_DEFAULT_BLOCKS_ROOT = Path(__file__).resolve().parents[3] / "blocks"


def load_block_repository() -> BlockRepository:
    """Wire a FileSystemBlockLoader from src/blocks or FREELOADER_BLOCKS override."""
    blocks_root = os.getenv("FREELOADER_BLOCKS")
    path = Path(blocks_root) if blocks_root else _DEFAULT_BLOCKS_ROOT
    assert path.is_dir(), f"Blocks root does not exist: {path}"
    return FileSystemBlockLoader.init(path)


def load_secrets_reader() -> SecretsReader:
    """Wire the default SecretsReader for block operations."""
    return SecretsAdapter()
