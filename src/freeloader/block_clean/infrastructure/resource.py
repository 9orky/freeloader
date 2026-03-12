from pathlib import Path
from shutil import rmtree


class ProvisioningResource:
    """Ephemeral Terraform workspace directory for one block during provisioning."""

    def __init__(self, folder: Path) -> None:
        folder.mkdir(parents=True, exist_ok=True)
        self._folder = folder

    @property
    def folder(self) -> Path:
        return self._folder

    def rm(self) -> None:
        if self._folder.is_dir():
            rmtree(self._folder)
