from pathlib import Path

from ..adapters import block_gateway, manifest_store


def forget_project(project_folder: Path) -> None:
    manifest = manifest_store.load_manifest(project_folder)
    block_gateway.destroy_project(
        project_folder,
        manifest_store.resources_folder(project_folder),
        manifest.blocks,
    )
    manifest_store.delete_project_state(project_folder)
