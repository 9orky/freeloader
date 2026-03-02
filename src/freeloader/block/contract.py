from typing import Any, Literal

from pydantic import BaseModel

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

    @property
    def required_secret_keys(self) -> list[str]:
        return [f.name for f in self.config if f.group == "secrets"]

    def config_fields(self, group: str) -> list[ConfigField]:
        return [f for f in self.config if f.group == group]
    
    def collect_defaults(self, groups: list[str]) -> dict[str, Any]:
        return {
            f.name: f.default 
            for f in self.config 
            if f.group in groups and f.default is not None
        }

