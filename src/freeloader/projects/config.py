from pathlib import Path

from freeloader.projects.models import GlobalConfig
from freeloader.shared.paths import config_path
from freeloader.shared.yaml_io import load_yaml_model, save_yaml_model


class ConfigLoader:
    def __init__(self, path: Path | None = None) -> None:
        self._path = path or config_path()

    def load(self) -> GlobalConfig:
        if not self._path.exists():
            return GlobalConfig()
        return load_yaml_model(self._path, GlobalConfig)

    def save(self, config: GlobalConfig) -> None:
        save_yaml_model(self._path, config)
