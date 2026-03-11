from pathlib import Path

import freeloader.block.ports.interface as block_interface
from freeloader.shared.types import ConfigValue

from ..models import TechStack


def get_manifest_configs(
    project_root: Path,
    tech_stack: TechStack | None,
    full_manifest: bool,
    project_name: str | None = None,
) -> dict[str, dict[str, ConfigValue]]:
    stack_data = tech_stack.model_dump(mode="python") if tech_stack else {}
    return block_interface.get_manifest_configs(
        project_root,
        stack_data,
        full_manifest,
        project_name,
    )


def provision_project(
    project_root: Path,
    resources_root: Path,
    block_refs: list[object],
) -> None:
    block_interface.provision_project(project_root, resources_root, block_refs)


def destroy_project(
    project_root: Path,
    resources_root: Path,
    block_refs: list[object],
) -> None:
    block_interface.destroy_project(project_root, resources_root, block_refs)
