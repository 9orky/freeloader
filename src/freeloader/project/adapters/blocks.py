import os
from pathlib import Path

from freeloader.block import Blocks, SecretsReader
from freeloader.secrets import read_secrets, has_secrets


class SecretsAdapter(SecretsReader):
    def has_secrets(self, secret_names: list[str]) -> bool:
        return has_secrets(secret_names, "global")  

    def read(self, secret_names: list[str]) -> dict[str, str]:
        return read_secrets("global", secret_names)


class BlocksAdapter:
    def __init__(self, project_root: Path, root: Path | None = None) -> None:
        self._root = root or self._get_blocks_root()
        self._blocks = Blocks(project_root, self._root, SecretsAdapter())

    def _get_blocks_root(self) -> Path:
        blocks_root = os.getenv("FREELOADER_BLOCKS", None)
        assert blocks_root, "FREELOADER_BLOCKS environment variable must be set"

        blocks_root_path = Path(blocks_root)
        assert blocks_root_path.is_dir(), f"Blocks root path does not exist"

        return blocks_root_path

    def get_manifest_configs(self, full_config: bool) -> dict[str, dict[str, str]]:
        return self._blocks.get_manifest_configs(full_config)
    
    def provision(self, resources_root: Path,  block_refs: list[BlockRef]) -> None:
        self._blocks.provision_resources(resources_root, block_refs)