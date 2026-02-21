from typing import Any, Literal

from pydantic import BaseModel, model_validator

from .layer import Layer


class BlockMeta(BaseModel):
    description: str = ""
    layer: Layer


class ConfigField(BaseModel):
    name: str
    description: str = ""
    required: bool = False
    default: str | int | float | bool | list[str] | None = None
    choices: list[str] | None = None
    group: Literal["basic", "advanced", "secrets"] = "basic"
    project_name_default: bool = False


class PortSpec(BaseModel):
    description: str = ""
    optional: bool = False
    sensitive: bool = False


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
    
    def collect_defaults(self, groups: list[str]) -> dict[str, Any]:
        return {
            f.name: f.default 
            for f in self.config 
            if f.group in groups and f.default is not None
        }


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
