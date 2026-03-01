from pathlib import Path

from ..adapters import BlocksAdapter

from .user.project import UserProject


def provision(cwd: Path):
    user_project = UserProject.from_path(cwd)
    manifest = user_project.manifest

    block_refs = manifest.blocks
    blocks_adapter = BlocksAdapter(cwd)

    blocks_adapter.provision_project(
        user_project.resources_folder,
        block_refs,
    )
