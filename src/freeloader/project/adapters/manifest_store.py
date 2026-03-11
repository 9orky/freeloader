import shutil
from pathlib import Path

from pydantic import BaseModel

from freeloader import block
from freeloader.shared import io
from freeloader.shared.types import ConfigValue

from ..models import TechStack

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


def manifest_exists(folder: Path) -> bool:
    return _manifest_path(folder).is_file()


def resources_folder(folder: Path) -> Path:
    return folder / ".freeloader"


def load_manifest(folder: Path) -> ManifestContract:
    manifest_path = _manifest_path(folder)
    assert manifest_path.is_file(), f"Project manifest not found in {folder}"
    return io.load_yaml_model(manifest_path, ManifestContract)


def save_manifest(
    name: str,
    folder: Path,
    stack: TechStack | None,
    block_configs: dict[str, dict[str, ConfigValue]],
) -> None:
    manifest_path = _manifest_path(folder)
    assert not manifest_path.is_file(
    ), f"Project manifest already exists in {folder}"

    resources_folder(folder).mkdir(exist_ok=True)
    manifest = ManifestContract.model_validate(
        {
            "project": _create_meta(name),
            "stack": _create_stack(stack),
            "blocks": _create_block_refs(block_configs),
        }
    )
    io.save_yaml_model(manifest_path, manifest)


def delete_project_state(folder: Path) -> None:
    manifest_path = _manifest_path(folder)
    assert manifest_path.is_file(
    ), f"Project manifest {manifest_path} does not exist"
    manifest_path.unlink()

    project_resources = resources_folder(folder)
    if project_resources.is_dir():
        shutil.rmtree(project_resources)


def _manifest_path(folder: Path) -> Path:
    return folder / _MANIFEST_FILE_NAME


def _create_block_refs(block_configs: dict[str, dict[str, ConfigValue]]) -> list[block.BlockRef]:
    return [block.BlockRef.model_validate({"use": name, "config": config}) for name, config in block_configs.items()]


def _create_stack(stack: TechStack | None) -> ManifestTechStack:
    stack_data = stack.model_dump(mode="python") if stack else {}
    return ManifestTechStack.model_validate(stack_data)


def _create_meta(name: str, path: str | None = None) -> ManifestMeta:
    return ManifestMeta(name=name, path=path)
