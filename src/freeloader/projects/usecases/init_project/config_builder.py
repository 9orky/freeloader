from freeloader.blocks.models import ConfigField
from freeloader.blocks.policies import build_config
from freeloader.blocks.registry import BlockRegistry


class ConfigBuilder:
    def __init__(self, registry: BlockRegistry) -> None:
        self._registry = registry

    def build(self, block_name: str, project_name: str, full: bool) -> dict[str, str]:
        fields = self._registry.get_config_fields(block_name)
        return build_config(fields, project_name, full)
