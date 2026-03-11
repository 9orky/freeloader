from dataclasses import dataclass
from pathlib import Path
from os import getenv

from eventsourcing.application import Application


@dataclass(frozen=True)
class Freeloader:
    cwd: Path
    home_folder: Path
    projects_folder: Path
    secrets_folder: Path
    session_folder: Path

    def build_managed_project_path(self, project_name: str) -> Path:
        return self.projects_folder / project_name

    @classmethod
    def resolve_home_folder(cls) -> Path:
        home_folder = Path(
            getenv("FREELOADER_HOME", str(Path.home() / ".freeloader")))
        home_folder.mkdir(parents=True, exist_ok=True)
        return home_folder

    @classmethod
    def resolve_db_path(cls) -> Path:
        db_path = Path(getenv("FREELOADER_DB", str(
            cls.resolve_home_folder() / "freeloader.db")))
        return db_path

    @classmethod
    def from_env(cls, cwd: Path) -> "Freeloader":
        home_folder = cls.resolve_home_folder()

        projects_folder = home_folder / "projects"
        projects_folder.mkdir(parents=True, exist_ok=True)

        secrets_folder = home_folder / "secrets"
        secrets_folder.mkdir(parents=True, exist_ok=True)

        session_folder = home_folder / "sessions"
        session_folder.mkdir(parents=True, exist_ok=True)

        return cls(
            cwd=cwd,
            home_folder=home_folder,
            projects_folder=projects_folder,
            secrets_folder=secrets_folder,
            session_folder=session_folder,
        )


class FreeloaderApplication(Application):
    env = {
        "INFRASTRUCTURE_FACTORY": "eventsourcing.sqlite:Factory",
        "SQLITE_DBNAME": str(Freeloader.resolve_db_path()),
    }


def hosts_path() -> Path:
    return Freeloader.resolve_home_folder() / "hosts"
