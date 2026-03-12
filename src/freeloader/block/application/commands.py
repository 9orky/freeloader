from collections.abc import Iterator
from pathlib import Path

from ..domain.events import BlockDestroyEvent, BlockProvisionEvent
from ..domain.entity import BlockRef
from ..domain.provisioning import DestroyReport, ProvisioningReport
from ..infrastructure import load_block_repository, load_block_runner
from .services.provisioner import BlockProvisioningService


def provision_blocks(
    project_root: Path,
    resources_root: Path,
    block_refs: list[BlockRef],
) -> ProvisioningReport:
    repository = load_block_repository()
    runner = load_block_runner(project_root)
    service = BlockProvisioningService(repository, runner)
    return service.provision(resources_root, block_refs)


def provision_blocks_events(
    project_root: Path,
    resources_root: Path,
    block_refs: list[BlockRef],
) -> Iterator[BlockProvisionEvent]:
    repository = load_block_repository()
    runner = load_block_runner(project_root)
    service = BlockProvisioningService(repository, runner)
    return service.provision_events(resources_root, block_refs)


def destroy_blocks(
    project_root: Path,
    resources_root: Path,
    block_refs: list[BlockRef],
) -> DestroyReport:
    repository = load_block_repository()
    runner = load_block_runner(project_root)
    service = BlockProvisioningService(repository, runner)
    return service.destroy(resources_root, block_refs)


def destroy_blocks_events(
    project_root: Path,
    resources_root: Path,
    block_refs: list[BlockRef],
) -> Iterator[BlockDestroyEvent]:
    repository = load_block_repository()
    runner = load_block_runner(project_root)
    service = BlockProvisioningService(repository, runner)
    return service.destroy_events(resources_root, block_refs)
