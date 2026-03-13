from collections.abc import Iterator
from pathlib import Path

from freeloader.shared.block import BlockDestroyEvent, BlockProvisionEvent
from freeloader.service_providers import ServiceProviders
from freeloader.shared.types import ConfigValue

from ..domain.entity import Manifest, TechStack
from ..infrastructure import load_block_gateway, load_manifest_repository, load_tech_stack_detector


def manage_project(name: str, folder: Path, full_manifest: bool = False) -> Manifest:
    manifest_repo = load_manifest_repository()
    detector = load_tech_stack_detector()
    block_gw = load_block_gateway()
    service_providers = ServiceProviders()

    assert folder.is_dir(), f"{folder} is not a directory"
    assert not manifest_repo.manifest_exists(folder), "Manifest already exists"

    tech_stack = detector.detect(folder) or TechStack()
    block_configs = block_gw.get_manifest_configs(
        folder, tech_stack, full_manifest, name)
    block_configs = _filter_supported_block_configs(
        block_configs, service_providers)
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


def _filter_supported_block_configs(
    block_configs: dict[str, dict[str, ConfigValue]],
    service_providers: ServiceProviders,
) -> dict[str, dict[str, ConfigValue]]:
    support_cache: dict[str, bool] = {}
    supported_configs: dict[str, dict[str, ConfigValue]] = {}

    for block_id, config in block_configs.items():
        driver_name = _provider_name_from_block_id(block_id)
        if driver_name not in support_cache:
            support_cache[driver_name] = service_providers.is_block_supported([
                                                                              driver_name])
        if support_cache[driver_name]:
            supported_configs[block_id] = config

    return supported_configs


def _provider_name_from_block_id(block_id: str) -> str:
    provider_name, separator, _ = block_id.partition(".")
    if not separator:
        raise ValueError(
            f"Invalid block id '{block_id}', expected format 'provider.block'"
        )
    return provider_name
