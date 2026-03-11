import os
from dataclasses import dataclass
from pathlib import Path

from freeloader.secrets.ports.interface import Secrets
from freeloader.shared.types import ConfigValue

from ..base import SecretsReader
from ..facade import BlocksFacade
from ..resolver import BlockRef


@dataclass(frozen=True)
class _SecretsAdapter(SecretsReader):
    secrets: Secrets = Secrets.for_default_namespace()

    def has_secrets(self, secret_names: list[str]) -> bool:
        return self.secrets.has_secrets(secret_names)

    def read(self, secret_names: list[str]) -> dict[str, str]:
        return self.secrets.read_secrets(secret_names)


def get_manifest_configs(
    project_root: Path,
    tech_stack: dict[str, str],
    full_config: bool,
    project_name: str | None = None,
) -> dict[str, dict[str, ConfigValue]]:
    return _build_facade(project_root).get_manifest_configs(
        tech_stack,
        full_config,
        project_name,
    )


def provision_project(
    project_root: Path,
    resources_root: Path,
    block_refs: list[BlockRef],
) -> None:
    _build_facade(project_root).provision(resources_root, block_refs)


def destroy_project(
    project_root: Path,
    resources_root: Path,
    block_refs: list[BlockRef],
) -> None:
    _build_facade(project_root).destroy(resources_root, block_refs)


def _build_facade(project_root: Path) -> BlocksFacade:
    return BlocksFacade(
        project_root,
        _blocks_root(),
        _SecretsAdapter(),
    )


def _blocks_root() -> Path:
    blocks_root = os.getenv("FREELOADER_BLOCKS")
    assert blocks_root, "FREELOADER_BLOCKS environment variable must be set"

    blocks_root_path = Path(blocks_root)
    assert blocks_root_path.is_dir(), f"Blocks root path does not exist"
    return blocks_root_path