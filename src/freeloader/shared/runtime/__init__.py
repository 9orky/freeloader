from dataclasses import dataclass
from pathlib import Path
from os import getenv


@dataclass(frozen=True)
class Freeloader:
    cwd: Path

    @property
    def home_folder(self) -> Path:
        home_folder = Path(getenv("FREELOADER_HOME", str(Path.home() / ".freeloader")))
        home_folder.mkdir(parents=True, exist_ok=True)
        return home_folder

    @property
    def secrets_folder(self) -> Path:
        secrets_folder = self.home_folder / "secrets"
        secrets_folder.mkdir(parents=True, exist_ok=True)
        return secrets_folder
    
    @property
    def session_folder(self) -> Path:
        session_folder = self.home_folder / "sessions"
        session_folder.mkdir(parents=True, exist_ok=True)
        return session_folder

    @classmethod
    def from_env(cls, cwd: Path | None = None) -> "Freeloader":
        if cwd is None:
            cwd = Path.cwd()

        assert cwd.is_dir(), f"Provided path '{cwd}' is not a directory"
        return cls(cwd=cwd)
