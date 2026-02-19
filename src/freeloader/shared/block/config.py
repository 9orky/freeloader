from pydantic import BaseModel

from .registry import BlockRegistry
from .models import PortSpec

NAME_FIELDS = ("name", "app_name")


class ConfigField(BaseModel):
    type: str = "string"
    required: bool = False
    default: str | int | float | bool | list[str] | None = None
    description: str = ""
    choices: list[str] | None = None


class BlockMeta(BaseModel):
    description: str = ""
    runner: str
    layer: str
    provider: str
    required_secrets: list[str] = []


class BlockContract(BaseModel):
    block: BlockMeta
    provides: dict[str, PortSpec] = {}
    requires: dict[str, PortSpec] = {}
    config: dict[str, ConfigField] = {}

    def map_outputs(self, raw: dict[str, object]) -> dict[str, object]:
        outputs: dict[str, object] = {}
        for port_key in self.provides:
            tf_name = port_key.split(".")[-1]
            if tf_name in raw:
                outputs[port_key] = raw[tf_name]
        return outputs


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
