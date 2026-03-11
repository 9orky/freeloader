from pydantic import BaseModel, Field

from freeloader.shared.types import ConfigValue


class TechStack(BaseModel):
    language: str | None = None
    language_version: str | None = None
    package_manager: str | None = None
    framework: str | None = None


class ManageProjectResult(BaseModel):
    tech_stack: TechStack | None = None
    blocks_configs: dict[str, dict[str, ConfigValue]
                         ] = Field(default_factory=dict)
