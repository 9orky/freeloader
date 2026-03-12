import dataclasses
from pathlib import Path

import freeloader.block.ports.interface as block_interface
from freeloader.block import BlockRef
from freeloader.shared.types import ConfigValue

from ..domain.entities import TechStack
from ..domain.repository import BlockGateway


class BlockSystemGateway(BlockGateway):
    def get_manifest_configs(
        self,
        project_root: Path,
        tech_stack: TechStack,
        full_manifest: bool,
        project_name: str | None,
    ) -> dict[str, dict[str, ConfigValue]]:
        stack_dict = {
            k: v
            for k, v in dataclasses.asdict(tech_stack).items()
            if v is not None
        }
        return block_interface.get_manifest_configs(
            project_root, stack_dict, full_manifest, project_name
        )

    def provision(
        self,
        project_root: Path,
        resources_root: Path,
        block_refs: list[BlockRef],
    ) -> None:
        block_interface.provision_project(project_root, resources_root, block_refs)

    def destroy(
        self,
        project_root: Path,
        resources_root: Path,
        block_refs: list[BlockRef],
    ) -> None:
        block_interface.destroy_project(project_root, resources_root, block_refs)
