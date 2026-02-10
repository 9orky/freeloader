import os
from pathlib import Path

FREELOADER_HOME = Path(os.environ.get(
    "FREELOADER_HOME", Path.home() / ".freeloader"))


def ensure_home() -> Path:
    for sub in ("blocks", "projects", "catalog", "schemas", "assets/templates", "cache/tf-plugins", "hosts"):
        (FREELOADER_HOME / sub).mkdir(parents=True, exist_ok=True)
    return FREELOADER_HOME


def project_state_dir(project_name: str) -> Path:
    return FREELOADER_HOME / "projects" / project_name


def project_tf_dir(project_name: str) -> Path:
    return project_state_dir(project_name) / "tf"


def blocks_dir() -> Path:
    return FREELOADER_HOME / "blocks"


def config_path() -> Path:
    return FREELOADER_HOME / "config.yaml"


def secrets_path() -> Path:
    return FREELOADER_HOME / "secrets.enc"


def hosts_path() -> Path:
    return FREELOADER_HOME / "hosts.yaml"


def bundled_blocks_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "blocks" / "_catalog"
