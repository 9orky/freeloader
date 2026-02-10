from pathlib import Path

from freeloader.shared.errors import ConfigurationError


def validate_manifest_exists(manifest_path: Path | None) -> Path:
    if not manifest_path:
        raise ConfigurationError(
            "No freeloader.yaml found (searched upward from current directory).\n"
            "Run 'fl projects init' to create one."
        )
    return manifest_path


def validate_no_existing_manifest(project_dir: Path) -> None:
    if (project_dir / "freeloader.yaml").exists():
        raise ConfigurationError(
            f"freeloader.yaml already exists in {project_dir}.\n"
            "Remove it first or use a different directory."
        )
