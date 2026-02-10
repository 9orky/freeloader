from pathlib import Path

from freeloader.pipeline.blocks.models import BlockContract, ConfigField, RunnerType
from freeloader.shared.paths import blocks_dir, bundled_blocks_dir
from freeloader.shared.yaml_io import load_yaml_model


class BlockRegistry:
    def __init__(self, user_dir: Path | None = None, bundled_dir: Path | None = None) -> None:
        self._user_dir = user_dir or blocks_dir()
        self._bundled_dir = bundled_dir or bundled_blocks_dir()
        self._cache: dict[str, tuple[BlockContract, Path]] = {}

    def _scan(self) -> None:
        self._cache.clear()
        for source_dir in (self._bundled_dir, self._user_dir):
            if not source_dir.exists():
                continue
            for block_yaml in sorted(source_dir.glob("*/block.yaml")):
                folder_name = block_yaml.parent.name
                contract = load_yaml_model(block_yaml, BlockContract)
                contract = contract.model_copy(
                    update={"block": contract.block.model_copy(
                        update={"name": folder_name})}
                )
                self._cache[folder_name] = (contract, block_yaml.parent)

    def _ensure_loaded(self) -> None:
        if not self._cache:
            self._scan()

    def list_blocks(self) -> list[BlockContract]:
        self._ensure_loaded()
        return [c for c, _ in self._cache.values()]

    def default_blocks(self) -> list[BlockContract]:
        self._ensure_loaded()
        return [c for c, _ in self._cache.values() if c.block.default]

    def get_block(self, name: str) -> BlockContract:
        self._ensure_loaded()
        return self._cache[name][0]

    def get_block_dir(self, name: str) -> Path:
        self._ensure_loaded()
        return self._cache[name][1]

    def has_block(self, name: str) -> bool:
        self._ensure_loaded()
        return name in self._cache

    def get_config_fields(self, name: str) -> dict[str, ConfigField]:
        contract = self.get_block(name)
        if contract.config:
            return contract.config
        if contract.block.runner == RunnerType.terraform:
            return self._config_fields_from_terraform(name)
        return {}

    def _config_fields_from_terraform(self, name: str) -> dict[str, ConfigField]:
        from freeloader.pipeline.runners.terraform.file import TerraformFile
        tf_path = self.get_block_dir(name) / "main.tf"
        if not tf_path.exists():
            return {}
        tf = TerraformFile(tf_path)
        fields: dict[str, ConfigField] = {}
        for var in tf.variables:
            if var.sensitive:
                continue
            fields[var.name] = ConfigField(
                type=var.type,
                required=var.required,
                default=var.default,
                description=var.description,
            )
        return fields

    def reload(self) -> None:
        self._scan()
