from freeloader.shared.types import ConfigValue

from ..infrastructure import load_block_repository, load_secrets_reader

_TECH_STACK_KEYS = frozenset(
    {"language", "language_version", "package_manager", "framework"}
)


def get_manifest_configs(
    tech_stack: dict[str, str],
    full_config: bool,
    project_name: str | None = None,
) -> dict[str, dict[str, ConfigValue]]:
    repository = load_block_repository()
    secrets = load_secrets_reader()
    blocks = repository.load_all()
    configs: dict[str, dict[str, ConfigValue]] = {}

    for block_id, block in blocks.items():
        contract = block.contract

        required_secrets = contract.required_secret_keys
        if required_secrets and not secrets.has_secrets(required_secrets):
            continue

        tech_stack_field_names = [
            field.name for field in contract.config if field.name in _TECH_STACK_KEYS
        ]
        if contract.block.required_tech_stack and not _has_required_tech_stack(
            tech_stack_field_names, tech_stack
        ):
            continue

        groups = ["basic", "advanced"] if full_config else ["basic"]
        config: dict[str, ConfigValue] = {}
        for field in contract.config:
            if field.group not in groups:
                continue
            if field.project_name_default and project_name is not None:
                config[field.name] = project_name
            elif field.default is not None:
                config[field.name] = field.default

        if contract.block.required_tech_stack:
            config = _apply_tech_stack(
                config, tech_stack_field_names, tech_stack)

        configs[block_id] = config

    return configs


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


def _has_required_tech_stack(
    field_names: list[str],
    tech_stack: dict[str, str],
) -> bool:
    if not field_names:
        return False
    return all(tech_stack.get(field_name) is not None for field_name in field_names)
