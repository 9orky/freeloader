from collections.abc import Iterator
from pathlib import Path

from freeloader.shared.block import BlockDestroyEvent, BlockProvisionEvent, BlockRef
from freeloader.shared.types import ConfigValue

from ..domain.provisioning import DestroyReport, ProvisioningReport

from . import commands, queries


class Blocks:
    def __init__(self, project_root: Path) -> None:
        self._project_root = project_root

    @classmethod
    def for_project(cls, project_root: Path) -> "Blocks":
        """Construct a Blocks facade scoped to one project root."""
        return cls(project_root=project_root)

    def manifest_configs(
        self,
        tech_stack: dict[str, str],
        full_config: bool,
        project_name: str | None = None,
    ) -> dict[str, dict[str, ConfigValue]]:
        return queries.get_manifest_configs(
            tech_stack=tech_stack,
            full_config=full_config,
            project_name=project_name,
        )

    def provision(
        self,
        resources_root: Path,
        block_refs: list[BlockRef],
    ) -> ProvisioningReport:
        return commands.provision_blocks(
            project_root=self._project_root,
            resources_root=resources_root,
            block_refs=block_refs,
        )

    def provision_events(
        self,
        resources_root: Path,
        block_refs: list[BlockRef],
    ) -> Iterator[BlockProvisionEvent]:
        return commands.provision_blocks_events(
            project_root=self._project_root,
            resources_root=resources_root,
            block_refs=block_refs,
        )

    def destroy(
        self,
        resources_root: Path,
        block_refs: list[BlockRef],
    ) -> DestroyReport:
        return commands.destroy_blocks(
            project_root=self._project_root,
            resources_root=resources_root,
            block_refs=block_refs,
        )

    def destroy_events(
        self,
        resources_root: Path,
        block_refs: list[BlockRef],
    ) -> Iterator[BlockDestroyEvent]:
        return commands.destroy_blocks_events(
            project_root=self._project_root,
            resources_root=resources_root,
            block_refs=block_refs,
        )
