from pathlib import Path

import freeloader.block.ports.interface as block_interface
from freeloader.shared.tech import TechFacade

from .user import UserProject


def manage_project(name: str, project_folder: Path, full_manifest: bool = False) -> dict:
    user_project = UserProject(name, project_folder)
    assert user_project.no_manifest(), "Manifest already exists"

    tech_stack = TechFacade().detect_stack(project_folder)
    blocks_configs = block_interface.get_manifest_configs(
        project_folder,
        tech_stack,
        full_manifest,
        name,
    )

    user_project.save_manifest(tech_stack, blocks_configs)
    return {"tech_stack": tech_stack, "blocks_configs": blocks_configs}
