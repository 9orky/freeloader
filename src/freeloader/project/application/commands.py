from pathlib import Path

from ..domain.entities import Manifest, TechStack
from ..infrastructure import load_block_gateway, load_manifest_repository, load_tech_stack_detector


def manage_project(name: str, folder: Path, full_manifest: bool = False) -> Manifest:
    manifest_repo = load_manifest_repository()
    detector = load_tech_stack_detector()
    block_gw = load_block_gateway()

    assert folder.is_dir(), f"{folder} is not a directory"
    assert not manifest_repo.manifest_exists(folder), "Manifest already exists"

    tech_stack = detector.detect(folder) or TechStack()
    block_configs = block_gw.get_manifest_configs(
        folder, tech_stack, full_manifest, name)
    manifest_repo.save(name, folder, tech_stack, block_configs)
    return manifest_repo.load(folder)


def provision_project(folder: Path) -> None:
    manifest_repo = load_manifest_repository()
    block_gw = load_block_gateway()
    manifest = manifest_repo.load(folder)
    block_gw.provision(folder, manifest_repo.resources_folder(
        folder), list(manifest.block_refs))


def forget_project(folder: Path) -> None:
    manifest_repo = load_manifest_repository()
    block_gw = load_block_gateway()
    manifest = manifest_repo.load(folder)
    block_gw.destroy(folder, manifest_repo.resources_folder(
        folder), list(manifest.block_refs))
    manifest_repo.delete(folder)
