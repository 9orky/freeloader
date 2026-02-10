from freeloader.pipeline.blocks.models import ConfigField
from freeloader.pipeline.blocks.registry import BlockRegistry

NAME_FIELDS = ("name", "app_name")


class ConfigBuilder:
    def __init__(self, registry: BlockRegistry) -> None:
        self._registry = registry

    def build(self, block_name: str, project_name: str, full: bool) -> dict[str, str]:
        fields = self._registry.get_config_fields(block_name)
        config: dict[str, str] = {}
        for field_name, field_spec in fields.items():
            if field_spec.required:
                config[field_name] = project_name if field_name in NAME_FIELDS else ""
            elif full:
                config[field_name] = str(
                    field_spec.default) if field_spec.default is not None else ""
        return config
