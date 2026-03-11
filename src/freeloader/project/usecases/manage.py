from pathlib import Path

from ..adapters import block_gateway, manifest_store, tech_stack as tech_stack_adapter
from ..models import ManageProjectResult, TechStack


def manage_project(name: str, project_folder: Path, full_manifest: bool = False) -> ManageProjectResult:
    project_folder = Path(project_folder)
    assert project_folder.is_dir(), f"Path {project_folder} is not a directory"
    assert not manifest_store.manifest_exists(
        project_folder), "Manifest already exists"

    tech_stack = tech_stack_adapter.detect_stack(project_folder)
    if tech_stack is None:
        tech_stack = TechStack()

    blocks_configs = block_gateway.get_manifest_configs(
        project_folder,
        tech_stack,
        full_manifest,
        name,
    )

    manifest_store.save_manifest(
        name, project_folder, tech_stack, blocks_configs)
    return ManageProjectResult(tech_stack=tech_stack, blocks_configs=blocks_configs)
