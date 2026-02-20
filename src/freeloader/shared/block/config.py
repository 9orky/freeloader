from typing import Any

from pydantic import BaseModel, model_validator

from .models import ConfigField, Layer, PortSpec


class BlockMeta(BaseModel):
    description: str = ""
    layer: Layer


class BlockContract(BaseModel):
    block: BlockMeta
    provides: dict[str, PortSpec] = {}
    requires: dict[str, PortSpec] = {}
    config: list[ConfigField] = []

    @model_validator(mode="before")
    @classmethod
    def _flatten_config(cls, data: Any) -> Any:
        raw_config = data.get("config")
        if not isinstance(raw_config, dict):
            return data
        fields: list[dict[str, Any]] = []
        for group in ("basic", "advanced", "secrets"):
            for entry in raw_config.get(group, []):
                fields.append({**entry, "group": group})
        return {**data, "config": fields}

    def map_outputs(self, raw: dict[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key in self.provides:
            if key not in raw:
                continue
            value = raw[key]
            if isinstance(value, dict) and "value" in value:
                result[key] = value["value"]
            else:
                result[key] = value
        return result

    def config_fields(self, group: str) -> list[ConfigField]:
        return [f for f in self.config if f.group == group]


class ConfigBuilder:
    def __init__(self, contracts: dict[str, BlockContract]) -> None:
        self._contracts = contracts

    def build(
        self,
        block_id: str,
        project_name: str,
        full: bool = False,
    ) -> dict[str, Any]:
        contract = self._contracts[block_id]
        groups = {"basic", "advanced"} if full else {"basic"}
        result: dict[str, Any] = {}
        for field in contract.config:
            if field.group not in groups:
                continue
            if field.group == "secrets":
                continue
            if field.project_name_default or (field.required and field.default is None):
                result[field.name] = project_name
            elif field.default is not None:
                result[field.name] = field.default
        return result
