from pathlib import Path

from freeloader.shared.types import ConfigValue

from .base import SecretsReader
from .infrastructure import BlockLoader
from .orchestrator import ConfigOrchestrator
from .resolver import BlockRef
from .provisioner import Provisioner
from .runner import BlockRunner


class BlocksFacade:
    def __init__(
        self,
        project_root: Path,
        blocks_root: Path,
        secrets: SecretsReader,
    ) -> None:
        self._loader = BlockLoader.init(blocks_root)
        self._runner = BlockRunner(project_root, secrets)
        self._orchestrator = ConfigOrchestrator(secrets)

    def get_manifest_configs(
        self,
        tech_stack: dict[str, str],
        full_config: bool,
        project_name: str | None = None,
    ) -> dict[str, dict[str, ConfigValue]]:
        return self._orchestrator.build_manifest_configs(
            self._loader.all_blocks,
            tech_stack,
            full_config,
            project_name,
        )

    def provision(self, resources_root: Path, block_refs: list[BlockRef]):
        provisioner = Provisioner(resources_root, self._loader, self._runner)
        provisioner.provision(block_refs)

    def destroy(self, resources_root: Path, block_refs: list[BlockRef]):
        provisioner = Provisioner(resources_root, self._loader, self._runner)
        provisioner.destroy(block_refs)
