from freeloader.blocks.models import BlockContract
from freeloader.blocks.registry import BlockRegistry
from freeloader.shared.errors import ConfigurationError


def validate_block_exists(name: str, registry: BlockRegistry) -> BlockContract:
    if not registry.has_block(name):
        raise ConfigurationError(
            f"Block '{name}' not found in catalog.\n"
            f"Run 'fl blocks list' to see available blocks."
        )
    return registry.get_block(name)


def filter_by_layer(contracts: list[BlockContract], layer: str | None) -> list[BlockContract]:
    if not layer:
        return contracts
    return [c for c in contracts if c.block.layer.value == layer]
