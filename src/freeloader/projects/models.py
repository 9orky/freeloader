from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, computed_field


class ProviderConfig(BaseModel):
    api_url: str | None = None
    extra: dict[str, str] = {}


class Defaults(BaseModel):
    github_org: str | None = None
    gitlab_username: str | None = None
    registry_provider: str | None = None
    deploy_provider: str | None = None


class GlobalConfig(BaseModel):
    defaults: Defaults = Field(default_factory=Defaults)
    providers: dict[str, ProviderConfig] = {}


class ProjectInfo(BaseModel):
    name: str
    description: str = ""
    source_dir: str = "."


class BlockRef(BaseModel):
    use: str
    id: str | None = None
    config: dict[str, Any] = {}

    @computed_field
    @property
    def resolved_id(self) -> str:
        return self.id or self.use


class ProjectManifest(BaseModel):
    project: ProjectInfo
    blocks: list[BlockRef]


class BlockStatus(str, Enum):
    pending = "pending"
    created = "created"
    failed = "failed"
    destroyed = "destroyed"


class BlockState(BaseModel):
    block_name: str
    block_use: str
    status: BlockStatus = BlockStatus.pending
    outputs: dict[str, Any] = {}
    last_applied: datetime | None = None
    error: str | None = None


class ProjectState(BaseModel):
    project_name: str
    blocks: list[BlockState] = []
    last_up: datetime | None = None
    last_down: datetime | None = None
