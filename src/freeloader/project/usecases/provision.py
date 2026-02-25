from pathlib import Path

from freeloader import block

from .system.managed_project import ManagedProject
from .user.project import UserProject


def provision(cwd: Path):
    user_project = UserProject.from_path(cwd)
    managed_project = ManagedProject.load(user_project.folder)


def _read_blocks_from_manifest(user_project: UserProject) -> list[block.BlockRef]:
    manifest = user_project.load_manifest()
    return manifest.blocks
