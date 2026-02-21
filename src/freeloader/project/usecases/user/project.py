from pathlib import Path
from typing import Any

from .manifest import ProjectManifest


class UserProject:
    def __init__(self, name: str, folder: Path):
        assert folder.is_dir(), f"Path {folder} is not a directory"
        self._name = name
        self._folder = folder

    def is_initialized(self) -> bool:
        return ProjectManifest.exists(self._folder)
    
    def save_manifest(self, block_configs: dict[str, Any]) -> None:
        ProjectManifest.create(self._folder, self._name, block_configs)

    def load_manifest(self) -> ProjectManifest:
        return ProjectManifest.load(self._folder)

    def search_files(self, pattern: str) -> list[Path]:
        return list(self._folder.glob(pattern))

    def has_file(self, glob_pattern: str) -> bool:
        return any(self._folder.glob(glob_pattern))

    def store_file(self, relative_path: str, content: str) -> Path:
        file_path = self._folder / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return file_path
