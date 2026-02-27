from pathlib import Path

from freeloader import tech

from ..adapters import BlocksAdapter

from .user import UserProject


def manage_project(name: str, project_folder: Path, full_manifest: bool = False) -> None:
    user_project = UserProject(name, project_folder)
    assert user_project.no_manifest(), "Manifest already exists"

    tech_stack = tech.detect(user_project.folder)
    blocks_configs = BlocksAdapter(project_folder).get_manifest_configs(full_manifest)

    user_project.save_manifest(tech_stack.to_dict(), blocks_configs)
