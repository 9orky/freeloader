from pathlib import Path

from .manifest import load_manifest, ProjectManifest


class ProjectFolder:
    def __init__(self, path: Path):
        self._path = path
        assert self._path.is_dir(), f"Project path {self._path} is not a directory"
        
    def load_manifest(self) -> ProjectManifest:
        return load_manifest(self._path)

    def search_files(self, pattern: str) -> list[Path]:
        return list(self._path.glob(pattern))
    
    def has_file(self, glob_pattern: str) -> bool:
        return any(self._path.glob(glob_pattern))
    
    def store_file(self, relative_path: str, content: str) -> Path:
        file_path = self._path / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        return file_path
