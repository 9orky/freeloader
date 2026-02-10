from pydantic import BaseModel, Field


class HostEntry(BaseModel):
    alias: str
    host: str
    user: str = "root"
    port: int = 22
    identity_file: str = "~/.ssh/id_ed25519"
    tags: list[str] = Field(default_factory=list)


class HostInventory(BaseModel):
    hosts: list[HostEntry] = Field(default_factory=list)
