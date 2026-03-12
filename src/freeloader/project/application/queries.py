from pathlib import Path

from ..domain.entities import Manifest, TechStack
from ..infrastructure import load_manifest_repository, load_tech_stack_detector


def detect_stack(folder: Path) -> TechStack | None:
    return load_tech_stack_detector().detect(folder)


def get_status(folder: Path) -> Manifest | None:
    manifest_repo = load_manifest_repository()
    if not manifest_repo.manifest_exists(folder):
        return None
    return manifest_repo.load(folder)
