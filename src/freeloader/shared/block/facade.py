from pathlib import Path
from os import getenv
from .base import BlockId, BlockRepository


class Blocks:
    def __init__(self, blocks_root: Path | None = None) -> None:
        folder = blocks_root or Path(getenv("FREELOADER_BLOCKS", None))
        self._repository = BlockRepository.load(folder)

    def get_manifest_configs(self, provider_names: list[str], full_config: bool) -> dict[str, dict[str, str]]:
        assert provider_names, "At least one provider name must be specified"

        providers = self._repository.get_by_names(provider_names)
        assert providers, f"No block providers found for names: {provider_names}"

        configs = {}
        for provider in providers:
            for block in provider.blocks:
                configs[block.id] = block.dump_config(full=full_config)
        return configs
    
    def provision_resource(self, block_id: BlockId, config: dict[str, str]) -> dict[str, str]:
        block = self._repository.get_by_id(block_id)
        return block.provision(config)


interface = Blocks()
