from pathlib import Path

from ..domain.entity import BlockRef
from ..infrastructure import load_block_repository, load_secrets_reader
from ..infrastructure.runner import BlockRunner

from .services.provisioner import (
    BlockProvisioningService,
    DestroyReport,
    ProvisioningReport,
)


def provision_blocks(
    project_root: Path,
    resources_root: Path,
    block_refs: list[BlockRef],
) -> ProvisioningReport:
    repository = load_block_repository()
    runner = BlockRunner(project_root, load_secrets_reader())
    service = BlockProvisioningService(repository, runner)
    return service.provision(resources_root, block_refs)


def destroy_blocks(
    project_root: Path,
    resources_root: Path,
    block_refs: list[BlockRef],
) -> DestroyReport:
    repository = load_block_repository()
    runner = BlockRunner(project_root, load_secrets_reader())
    service = BlockProvisioningService(repository, runner)
    return service.destroy(resources_root, block_refs)
