from pathlib import Path

import freeloader.block.ports.interface as block_interface

from .user.project import UserProject


def forget_project(cwd: Path):
    user_project = UserProject.from_path(cwd)
    manifest = user_project.manifest

    block_interface.destroy_project(
        cwd,
        user_project.resources_folder,
        manifest.blocks,
    )

    user_project.clean_up()
