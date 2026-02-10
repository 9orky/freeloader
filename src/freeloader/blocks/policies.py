from freeloader.blocks.models import BlockContract, ConfigField
from freeloader.blocks.registry import BlockRegistry
from freeloader.shared.errors import ConfigurationError

NAME_FIELDS = ("name", "app_name")


def validate_block_exists(name: str, registry: BlockRegistry) -> BlockContract:
    if not registry.has_block(name):
        available = ", ".join(c.block.name for c in registry.list_blocks())
        raise ConfigurationError(
            f"Block '{name}' not found in catalog.\n"
            f"Available blocks: {available}\n"
            f"Run 'fl blocks list' to see details."
        )
    return registry.get_block(name)


def filter_by_layer(contracts: list[BlockContract], layer: str | None) -> list[BlockContract]:
    if not layer:
        return contracts
    return [c for c in contracts if c.block.layer.value == layer]


def build_config(
    fields: dict[str, ConfigField],
    project_name: str,
    full: bool,
) -> dict[str, str]:
    config: dict[str, str] = {}
    for field_name, field_spec in fields.items():
        if field_spec.required:
            config[field_name] = project_name if field_name in NAME_FIELDS else ""
        elif full:
            config[field_name] = str(
                field_spec.default) if field_spec.default is not None else ""
    return config


def validate_config(
    block_name: str,
    config: dict[str, str],
    fields: dict[str, ConfigField],
) -> None:
    for field_name, field_spec in fields.items():
        if field_spec.required and field_name not in NAME_FIELDS and not config.get(field_name):
            raise ConfigurationError(
                f"Block '{block_name}': required config field '{field_name}' is empty.\n"
                f"Set it in freeloader.yaml under the block's config section."
            )
        value = config.get(field_name)
        if value and field_spec.choices and value not in field_spec.choices:
            raise ConfigurationError(
                f"Block '{block_name}': config field '{field_name}' has invalid value '{value}'.\n"
                f"Allowed values: {', '.join(field_spec.choices)}"
            )
