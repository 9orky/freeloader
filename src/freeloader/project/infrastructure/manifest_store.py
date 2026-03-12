import shutil
from pathlib import Path

from pydantic import BaseModel

from freeloader import block
from freeloader.shared import io
from freeloader.shared.types import ConfigValue

from ..domain.entities import Manifest, TechStack
from ..domain.repository import ManifestRepository

_MANIFEST_FILE_NAME = "freeloader.yaml"
_RESOURCES_DIR_NAME = ".freeloader"


class _ManifestMeta(BaseModel):
    name: str
    description: str = ""
    path: str | None = None


class _ManifestTechStack(BaseModel):
    language: str | None = None
    language_version: str | None = None
    package_manager: str | None = None
    framework: str | None = None


class _ManifestContract(BaseModel):
    project: _ManifestMeta
    stack: _ManifestTechStack
    blocks: list[block.BlockRef]


class YamlManifestStore(ManifestRepository):
    def manifest_exists(self, folder: Path) -> bool:
        return self._manifest_path(folder).is_file()

    def load(self, folder: Path) -> Manifest:
        manifest_path = self._manifest_path(folder)
        assert manifest_path.is_file(
        ), f"Project manifest not found in {folder}"
        contract = io.load_yaml_model(manifest_path, _ManifestContract)
        tech_stack = TechStack(**contract.stack.model_dump())
        return Manifest(
            name=contract.project.name,
            tech_stack=tech_stack,
            block_refs=tuple(contract.blocks),
        )

    def save(
        self,
        name: str,
        folder: Path,
        tech_stack: TechStack,
        block_configs: dict[str, dict[str, ConfigValue]],
    ) -> None:
        manifest_path = self._manifest_path(folder)
        assert not manifest_path.is_file(
        ), f"Project manifest already exists in {folder}"
        self.resources_folder(folder).mkdir(exist_ok=True)
        block_refs = [
            block.BlockRef.model_validate({"use": ref_name, "config": config})
            for ref_name, config in block_configs.items()
        ]
        contract = _ManifestContract.model_validate({
            "project": {"name": name},
            "stack": tech_stack.to_dict(),
            "blocks": block_refs,
        })
        io.save_yaml_model(manifest_path, contract)

    def delete(self, folder: Path) -> None:
        manifest_path = self._manifest_path(folder)
        assert manifest_path.is_file(
        ), f"Project manifest {manifest_path} does not exist"
        manifest_path.unlink()
        resources = self.resources_folder(folder)
        if resources.is_dir():
            shutil.rmtree(resources)

    def resources_folder(self, folder: Path) -> Path:
        return folder / _RESOURCES_DIR_NAME

    def _manifest_path(self, folder: Path) -> Path:
        return folder / _MANIFEST_FILE_NAME
