from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field, computed_field

from ...shared import yaml_io


class BlockRef(BaseModel):
    use: str
    id: str | None = None
    config: dict[str, Any] = {}

    @computed_field
    @property
    def resolved_id(self) -> str:
        return self.id or self.use
    

class ManifestMeta(BaseModel):
    name: str
    description: str = ""


class ProjectManifest(BaseModel):
    project: ManifestMeta
    blocks: list[BlockRef]


def load_manifest(path: Path) -> ProjectManifest:
    manifest_path = path / "freeloader.yaml"
    assert manifest_path.is_file(), f"Project manifest {manifest_path} does not exist"

    manifest_dict = yaml_io.load_yaml(manifest_path)
    return ProjectManifest(**manifest_dict)