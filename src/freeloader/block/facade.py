from pathlib import Path

from .base import SecretsReader
from .infrastructure import BlockLoader
from .resolver import BlockRef
from .provisioner import Provisioner
from .runner import BlockRunner


class Blocks:
    def __init__(
        self, 
        project_root: Path,
        blocks_root: Path,
        secrets: SecretsReader,
    ) -> None:
        self._loader = BlockLoader.init(blocks_root)
        self._runner = BlockRunner(project_root, secrets)
        self._secrets = secrets

    def get_manifest_configs(self, full_config: bool) -> dict[str, dict[str, str]]:
        configs = {}
        for block_id, block in self._loader.all_blocks.items():
            required_secrets = block.contract.required_secret_keys
            if required_secrets and not self._secrets.has_secrets(required_secrets):
                continue
            
            config = block.dump_config(full_config)
            configs[block_id] = config
        return configs
    
    def provision_resources(self, resources_root: Path, block_refs: list[BlockRef]):
        provisioner = Provisioner(self._loader, self._runner)
        provisioner.provision(resources_root, block_refs)
