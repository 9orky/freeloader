from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from freeloader.secrets import Secrets
from freeloader.service_providers import ServiceProviders
from freeloader.shared.block import BlockDestroyEvent, BlockProvisionEvent

from ..domain.entity import Manifest, TechStack
from ..infrastructure import load_block_gateway, load_manifest_repository, load_tech_stack_detector
from .services import ProjectPlanner, SelectionContext, SelectionReport


@dataclass(frozen=True)
class ManagedProject:
    manifest: Manifest
    selection_report: SelectionReport


def manage_project(name: str, folder: Path, full_manifest: bool = False) -> Manifest:
    return manage_project_with_report(name, folder, full_manifest).manifest


def manage_project_with_report(name: str, folder: Path, full_manifest: bool = False) -> ManagedProject:
    manifest_repo = load_manifest_repository()
    detector = load_tech_stack_detector()
    block_gw = load_block_gateway()
    service_providers = ServiceProviders()
    secrets = Secrets.for_default_namespace()

    assert folder.is_dir(), f"{folder} is not a directory"
    assert not manifest_repo.manifest_exists(folder), "Manifest already exists"

    tech_stack = detector.detect(folder) or TechStack()
    planner = ProjectPlanner(block_gw, service_providers, secrets)
    selection_report = planner.plan(
        SelectionContext(
            name=name,
            folder=folder,
            tech_stack=tech_stack,
            full_manifest=full_manifest,
        )
    )
    manifest_repo.save(name, folder, tech_stack, selection_report.selected_configs)
    return ManagedProject(
        manifest=manifest_repo.load(folder),
        selection_report=selection_report,
    )


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
