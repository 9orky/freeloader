from pydantic import BaseModel, Field

from freeloader.shared.types import ConfigValue


class ProjectStatusView(BaseModel):
    is_managed: bool
    details: dict[str, str] = Field(default_factory=dict)


class ManageProjectView(BaseModel):
    tech_stack: dict | None = None
    block_configs: dict[str, dict[str, ConfigValue]] = Field(default_factory=dict)
