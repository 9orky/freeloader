from freeloader.shared.tech import TECH_STACK_FIELD_NAMES
from freeloader.shared.types import ConfigValue

from ..domain.entity import Block, BlockCandidate
from ..infrastructure import load_block_repository


def get_manifest_candidates(
    tech_stack: dict[str, str],
    full_config: bool,
    project_name: str | None = None,
) -> tuple[BlockCandidate, ...]:
    repository = load_block_repository()
    blocks = repository.load_all()
    return tuple(
        _manifest_candidate(block, tech_stack, full_config, project_name)
        for block in blocks.values()
    )


def _manifest_candidate(
    block: Block,
    tech_stack: dict[str, str],
    full_config: bool,
    project_name: str | None,
) -> BlockCandidate:
    contract = block.contract
    groups = ("basic", "advanced") if full_config else ("basic",)
    required_tech_fields = tuple(
        field.name for field in contract.config if field.name in TECH_STACK_FIELD_NAMES
    )
    config: dict[str, ConfigValue] = {}

    for field in contract.config:
        if field.group not in groups:
            continue
        if field.project_name_default and project_name is not None:
            config[field.name] = project_name
        elif field.default is not None:
            config[field.name] = field.default

    if contract.block.required_tech_stack:
        config = _apply_tech_stack(config, list(required_tech_fields), tech_stack)

    return BlockCandidate(
        id=block.id,
        provider=block.id.provider,
        config=config,
        required_secret_keys=tuple(contract.required_secret_keys),
        required_tech_fields=required_tech_fields,
        required_tech_stack=contract.block.required_tech_stack,
        config_groups=groups,
    )


def _apply_tech_stack(
    config: dict[str, ConfigValue],
    field_names: list[str],
    tech_stack: dict[str, str],
) -> dict[str, ConfigValue]:
    for field_name in field_names:
        value = tech_stack.get(field_name)
        if value is not None:
            config[field_name] = value
    return config
