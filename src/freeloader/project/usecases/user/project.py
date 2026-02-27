from pathlib import Path
import shutil
from typing import Any

from .manifest import ProjectManifest


class UserProject:
    def __init__(self, name: str, folder: Path):
        assert folder.is_dir(), f"Path {folder} is not a directory"
        self._name = name
        self._folder = folder

    @classmethod
    def from_path(cls, folder: Path) -> "UserProject":
        assert ProjectManifest.exists(folder), f"No project manifest found in {folder}"
        return cls(name=folder.name, folder=folder)

    @property
    def name(self) -> str:
        return self._name

    @property
    def folder(self) -> Path:
        return self._folder
    
    @property
    def resources_folder(self) -> Path:
        return self._folder / ".freeloader"
    
    @property
    def manifest(self) -> ProjectManifest:
        return ProjectManifest.load(self._folder)

    def no_manifest(self) -> bool:
        return not ProjectManifest.exists(self._folder)

    def save_manifest(self, stack: dict[str, Any], block_configs: dict[str, Any]) -> None:
        resources_dir = self._folder / ".freeloader"
        resources_dir.mkdir(exist_ok=True)
        ProjectManifest.create(self._name, self._folder, stack, block_configs)

    def clean_up(self) -> None:
        ProjectManifest.load(self._folder).delete()
        resources_dir = self._folder / ".freeloader"
        if resources_dir.is_dir():
            shutil.rmtree(resources_dir)
