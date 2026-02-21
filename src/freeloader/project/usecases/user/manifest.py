from pathlib import Path
from typing import Any
from pydantic import BaseModel
from dataclasses import dataclass

from freeloader import io, block


class ManifestMeta(BaseModel):
    name: str
    description: str = ""
    path: str | None = None


class ManifestContract(BaseModel):
    project: ManifestMeta
    blocks: list[block.BlockRef]


def _create_block_refs(block_configs: dict[str, Any]) -> list[block.BlockRef]:
    return [block.BlockRef.model_validate({"use": k, "config": v}) for k, v in block_configs.items()]


def _create_meta(name: str,  path: str | None = None) -> ManifestMeta:
    return ManifestMeta(name=name, path=path)


_MANIFEST_FILE_NAME = "freeloader.yaml"


@dataclass(frozen=True)
class ProjectManifest:
    manifest_file: Path

    @classmethod
    def exists(cls, folder: Path) -> bool:
        return (folder / _MANIFEST_FILE_NAME).is_file()
    
    @classmethod
    def create(cls, folder: Path, name: str, block_configs: dict[str, Any]) -> "ProjectManifest":
        assert not cls.exists(folder), f"Project manifest already exists in {folder}"

        data = {"project": _create_meta(name), "blocks": _create_block_refs(block_configs)}
        manifest = ManifestContract.model_validate(data)
        io.save_yaml_model(folder / _MANIFEST_FILE_NAME, manifest)
        
        return cls(manifest_file=folder / _MANIFEST_FILE_NAME)

    @classmethod
    def load(cls, folder: Path) -> "ProjectManifest":
        manifest_path = folder / _MANIFEST_FILE_NAME
        assert manifest_path.is_file(), f"Project manifest {manifest_path} does not exist"

        io.load_yaml_model(manifest_path, ManifestContract)
        return cls(manifest_file=manifest_path)
    
    @property
    def blocks(self) -> list[block.BlockRef]:
        contract = io.load_yaml_model(self.manifest_file, ManifestContract)
        return contract.blocks

