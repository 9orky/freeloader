from pathlib import Path
from os import getenv


class Freeloader:
    def __init__(self) -> None:
        home_folder = getenv("FREELOADER_HOME", str(Path.home() / ".freeloader"))
        home_folder_path = Path(home_folder)
        home_folder_path.mkdir(parents=True, exist_ok=True)
        
        self._root = home_folder_path
        self._projects_folder = self._root / "projects"
        self._secrets_folder = self._root / "secrets"

    @property
    def home(self) -> Path:
        return self._root
    
    @property
    def projects_folder(self) -> Path:
        return self._projects_folder

    @property
    def secrets_folder(self) -> Path:
        return self._secrets_folder

    def install(self):
        assert not self._projects_folder.exists(), "Projects folder already exists"
        assert not self._secrets_folder.exists(), "Secrets folder already exists"

        self._projects_folder.mkdir(parents=True, exist_ok=True)
        self._secrets_folder.mkdir(parents=True, exist_ok=True)

    def is_installed(self) -> bool:
        return self._projects_folder.exists() and self._secrets_folder.exists()
    
    def must_be_installed(self):
        if not self.is_installed():
            raise RuntimeError("Freeloader is not installed.")
    
    def build_managed_project_path(self, project_name: str) -> Path:
        return self._projects_folder / project_name