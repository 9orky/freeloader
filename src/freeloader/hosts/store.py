from pathlib import Path

from freeloader.hosts.models import HostEntry, HostInventory
from freeloader.shared.yaml_io import load_yaml_model, save_yaml_model


class HostStore:
    def __init__(self, path: Path) -> None:
        self._path = path

    def load(self) -> HostInventory:
        if not self._path.exists():
            return HostInventory()
        return load_yaml_model(self._path, HostInventory)

    def save(self, inventory: HostInventory) -> None:
        save_yaml_model(self._path, inventory)

    def add(self, entry: HostEntry) -> None:
        inventory = self.load()
        inventory.hosts = [
            h for h in inventory.hosts if h.alias != entry.alias]
        inventory.hosts.append(entry)
        self.save(inventory)

    def remove(self, alias: str) -> bool:
        inventory = self.load()
        before = len(inventory.hosts)
        inventory.hosts = [h for h in inventory.hosts if h.alias != alias]
        if len(inventory.hosts) == before:
            return False
        self.save(inventory)
        return True

    def get(self, alias: str) -> HostEntry | None:
        inventory = self.load()
        return next((h for h in inventory.hosts if h.alias == alias), None)

    def list_all(self) -> list[HostEntry]:
        return self.load().hosts
