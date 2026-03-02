from pathlib import Path

from ..adapters import BlocksAdapter

from .user.project import UserProject


def forget_project(cwd: Path):
    user_project = UserProject.from_path(cwd)
    manifest = user_project.manifest

    block_refs = manifest.blocks
    blocks_adapter = BlocksAdapter(cwd)

    blocks_adapter.destroy_project(
        user_project.resources_folder,
        block_refs,
    )

    user_project.clean_up()
