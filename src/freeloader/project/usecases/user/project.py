from pathlib import Path
from typing import Any

from .manifest import ProjectManifest


class UserProject:
    def __init__(self, name: str, folder: Path):
        assert folder.is_dir(), f"Path {folder} is not a directory"
        self._name = name
        self._folder = folder

    @classmethod
    def from_path(cls, folder: Path) -> "UserProject":
        manifest = folder / "freeloader.yaml"
        assert manifest.is_file(), f"No project manifest found in {folder}"
        return cls(name=folder.name, folder=folder)

    @property
    def name(self) -> str:
        return self._name
    
    @property
    def folder(self) -> Path:
        return self._folder

    def no_manifest(self) -> bool:
        return not ProjectManifest.exists(self._folder)
    
    def save_manifest(self, block_configs: dict[str, Any]) -> None:
        ProjectManifest.create(self._folder, self._name, block_configs)

    def load_manifest(self) -> ProjectManifest:
        return ProjectManifest.load(self._folder)
