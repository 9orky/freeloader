from dataclasses import dataclass
import os
from pathlib import Path

from freeloader.block import BlocksFacade, SecretsReader, BlockRef
from freeloader.secrets import Secrets


@dataclass(frozen=True)
class SecretsAdapter(SecretsReader):
    secrets: Secrets = Secrets.for_default_namespace()

    def has_secrets(self, secret_names: list[str]) -> bool:
        return self.secrets.has_secrets(secret_names)

    def read(self, secret_names: list[str]) -> dict[str, str]:
        return self.secrets.read_secrets(secret_names)


class BlocksAdapter:
    def __init__(self, project_root: Path, blocks_root: Path | None = None) -> None:
        blocks_root = blocks_root or self._get_blocks_root()
        self._blocks_facade = BlocksFacade(project_root, blocks_root, SecretsAdapter())

    def _get_blocks_root(self) -> Path:
        blocks_root = os.getenv("FREELOADER_BLOCKS", None)
        assert blocks_root, "FREELOADER_BLOCKS environment variable must be set"

        blocks_root_path = Path(blocks_root)
        assert blocks_root_path.is_dir(), f"Blocks root path does not exist"

        return blocks_root_path

    def get_manifest_configs(self, full_config: bool) -> dict[str, dict[str, str]]:
        return self._blocks_facade.get_manifest_configs(full_config)

    def provision_project(self, resources_root: Path,  block_refs: list[BlockRef]) -> None:
        self._blocks_facade.provision(resources_root, block_refs)

    def destroy_project(self, resources_root: Path,  block_refs: list[BlockRef]) -> None:
        self._blocks_facade.destroy(resources_root, block_refs)
