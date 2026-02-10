from pathlib import Path

from freeloader.projects.discovery import ProjectDiscovery
from freeloader.shared.errors import ConfigurationError

MANIFEST_NAME = ProjectDiscovery.MANIFEST_NAME


def validate_manifest_exists(manifest_path: Path | None) -> Path:
    if not manifest_path:
        raise ConfigurationError(
            f"No {MANIFEST_NAME} found (searched upward from current directory).\n"
            f"Run 'fl projects init' to create one."
        )
    return manifest_path


def validate_no_existing_manifest(project_dir: Path) -> None:
    if (project_dir / MANIFEST_NAME).exists():
        raise ConfigurationError(
            f"{MANIFEST_NAME} already exists in {project_dir}.\n"
            "Remove it first or use a different directory."
        )
