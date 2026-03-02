from typing import Literal

from pydantic import BaseModel, model_validator

from freeloader.shared.types import ConfigValue

from .layer import Layer

_TECH_STACK_KEYS = frozenset(
    {"language", "language_version", "package_manager", "framework"})


class BlockMeta(BaseModel):
    description: str = ""
    layer: Layer
    required_tech_stack: bool = False


class ConfigField(BaseModel):
    name: str
    description: str = ""
    required: bool = False
    default: ConfigValue | None = None
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
    def _flatten_config_groups(cls, data: dict) -> dict:
        raw = data.get("config")
        if not isinstance(raw, dict):
            return data
        flat: list[dict] = []
        for group_name in ("basic", "advanced", "secrets"):
            entries = raw.get(group_name)
            if not entries:
                continue
            for entry in entries:
                entry["group"] = group_name
                flat.append(entry)
        data["config"] = flat
        return data

    @property
    def required_secret_keys(self) -> list[str]:
        return [f.name for f in self.config if f.group == "secrets"]

    @property
    def tech_stack_field_names(self) -> list[str]:
        return [f.name for f in self.config if f.name in _TECH_STACK_KEYS]

    def config_fields(self, group: str) -> list[ConfigField]:
        return [f for f in self.config if f.group == group]

    def collect_defaults(
        self,
        groups: list[str],
        project_name: str | None = None,
    ) -> dict[str, ConfigValue]:
        result: dict[str, ConfigValue] = {}
        for f in self.config:
            if f.group not in groups:
                continue
            if f.project_name_default and project_name is not None:
                result[f.name] = project_name
            elif f.default is not None:
                result[f.name] = f.default
        return result
