from pathlib import Path

import freeloader.block.ports.interface as block_interface

from .user.project import UserProject


def provision(cwd: Path):
    user_project = UserProject.from_path(cwd)
    manifest = user_project.manifest

    block_interface.provision_project(
        cwd,
        user_project.resources_folder,
        manifest.blocks,
    )
