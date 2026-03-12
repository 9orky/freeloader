from collections.abc import Iterator
from pathlib import Path

from freeloader.block import BlockDestroyEvent, BlockProvisionEvent

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
    for _event in provision_project_events(folder):
        pass


def provision_project_events(folder: Path) -> Iterator[BlockProvisionEvent]:
    manifest_repo = load_manifest_repository()
    block_gw = load_block_gateway()
    manifest = manifest_repo.load(folder)
    resources_root = manifest_repo.resources_folder(folder)
    return block_gw.provision_events(folder, resources_root, list(manifest.block_refs))


def forget_project(folder: Path) -> None:
    for _event in forget_project_events(folder):
        pass


def forget_project_events(folder: Path) -> Iterator[BlockDestroyEvent]:
    manifest_repo = load_manifest_repository()
    block_gw = load_block_gateway()
    manifest = manifest_repo.load(folder)
    resources_root = manifest_repo.resources_folder(folder)

    def events() -> Iterator[BlockDestroyEvent]:
        yield from block_gw.destroy_events(folder, resources_root, list(manifest.block_refs))
        manifest_repo.delete(folder)

    return events()
