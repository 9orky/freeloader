from pathlib import Path
from typing import Any
from pydantic import BaseModel
from dataclasses import dataclass

from freeloader import io, block


_MANIFEST_FILE_NAME = "freeloader.yaml"


class ManifestMeta(BaseModel):
    name: str
    description: str = ""
    path: str | None = None


class ManifestTechStack(BaseModel):
    language: str
    language_version: str
    package_manager: str


class ManifestContract(BaseModel):
    project: ManifestMeta
    stack: ManifestTechStack
    blocks: list[block.BlockRef]


@dataclass(frozen=True)
class ProjectManifest:
    manifest_file: Path

    @classmethod
    def exists(cls, folder: Path) -> bool:
        return (folder / _MANIFEST_FILE_NAME).is_file()
    
    @classmethod
    def load(cls, folder: Path) -> "ProjectManifest":
        manifest_path = folder / _MANIFEST_FILE_NAME
        assert manifest_path.is_file(), f"Project manifest not found in {folder}"
        return cls(manifest_file=manifest_path)
    
    @classmethod
    def create(cls, name: str, folder: Path, stack: dict[str, Any], block_configs: dict[str, Any]) -> "ProjectManifest":
        assert not cls.exists(folder), f"Project manifest already exists in {folder}"

        manifest = ManifestContract.model_validate({
            "project": cls._create_meta(name), 
            "stack": cls._create_stack(stack), 
            "blocks": cls._create_block_refs(block_configs)
        })
        
        io.save_yaml_model(folder / _MANIFEST_FILE_NAME, manifest)
        return cls(manifest_file=folder / _MANIFEST_FILE_NAME)
    
    def delete(self) -> None:
        assert self.manifest_file.is_file(), f"Project manifest {self.manifest_file} does not exist"
        self.manifest_file.unlink()

    @property
    def contract(self) -> ManifestContract:
        manifest_path = self.manifest_file
        assert manifest_path.is_file(), f"Project manifest {manifest_path} does not exist"
        return io.load_yaml_model(manifest_path, ManifestContract)
    
    @property
    def blocks(self) -> list[block.BlockRef]:
        contract = io.load_yaml_model(self.manifest_file, ManifestContract)
        return contract.blocks

    @staticmethod
    def _create_block_refs(block_configs: dict[str, Any]) -> list[block.BlockRef]:
        return [block.BlockRef.model_validate({"use": k, "config": v}) for k, v in block_configs.items()]

    @staticmethod
    def _create_stack(stack: dict[str, Any]) -> ManifestTechStack:
        return ManifestTechStack.model_validate(stack)

    @staticmethod
    def _create_meta(name: str, path: str | None = None) -> ManifestMeta:
        return ManifestMeta(name=name, path=path)
