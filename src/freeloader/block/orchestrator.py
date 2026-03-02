from freeloader.shared.types import ConfigValue

from .base import SecretsReader
from .infrastructure import Block


class ConfigOrchestrator:
    def __init__(self, secrets: SecretsReader) -> None:
        self._secrets = secrets

    def build_manifest_configs(
        self,
        blocks: dict[str, Block],
        tech_stack: dict[str, str],
        full_config: bool,
        project_name: str | None = None,
    ) -> dict[str, dict[str, ConfigValue]]:
        configs: dict[str, dict[str, ConfigValue]] = {}

        for block_id, block in blocks.items():
            contract = block.contract

            required_secrets = contract.required_secret_keys
            if required_secrets and not self._secrets.has_secrets(required_secrets):
                continue

            config = block.dump_config(full_config, project_name)

            if contract.block.required_tech_stack and tech_stack:
                config = self._apply_tech_stack(
                    config, contract.tech_stack_field_names, tech_stack)

            configs[block_id] = config

        return configs

    @staticmethod
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
