import dataclasses
from collections.abc import Iterator
from pathlib import Path

from freeloader.block import Blocks
from freeloader.shared.block import BlockDestroyEvent, BlockProvisionEvent, BlockRef
from freeloader.shared.types import ConfigValue

from ..domain.entity import TechStack
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
        return Blocks.for_project(project_root).manifest_configs(
            stack_dict, full_manifest, project_name
        )

    def provision(
        self,
        project_root: Path,
        resources_root: Path,
        block_refs: list[BlockRef],
    ) -> None:
        Blocks.for_project(project_root).provision(resources_root, block_refs)

    def provision_events(
        self,
        project_root: Path,
        resources_root: Path,
        block_refs: list[BlockRef],
    ) -> Iterator[BlockProvisionEvent]:
        return Blocks.for_project(project_root).provision_events(resources_root, block_refs)

    def destroy(
        self,
        project_root: Path,
        resources_root: Path,
        block_refs: list[BlockRef],
    ) -> None:
        Blocks.for_project(project_root).destroy(resources_root, block_refs)

    def destroy_events(
        self,
        project_root: Path,
        resources_root: Path,
        block_refs: list[BlockRef],
    ) -> Iterator[BlockDestroyEvent]:
        return Blocks.for_project(project_root).destroy_events(resources_root, block_refs)
