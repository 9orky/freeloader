from pathlib import Path
from shutil import rmtree
from uuid import UUID
from typing import Iterator


class ManagedProject:
    resources_root = "resources"

    def __init__(self, folder: Path):
        self.folder = folder

    @classmethod
    def create(cls, projects_folder: Path, name: str, project_id: UUID) -> "ManagedProject":
        project_folder = projects_folder / name
        project_folder.mkdir()
        (project_folder / cls.resources_root).mkdir()
        (project_folder / "project_id").write_text(str(project_id))
        return cls(project_folder)

    @property
    def root(self) -> Path:
        return self.folder

    @property
    def resources_path(self) -> Path:
        return self.folder / self.resources_root

    @property
    def project_id(self) -> UUID:
        return UUID((self.folder / "project_id").read_text().strip())

    @classmethod
    def iter_all(cls, projects_folder: Path) -> Iterator["ManagedProject"]:
        for folder in projects_folder.iterdir():
            if folder.is_dir():
                yield cls(folder)

    def destroy(self):
        rmtree(self.folder)
