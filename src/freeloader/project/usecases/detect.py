from pathlib import Path

from freeloader.shared.tech import TechFacade


def detect_stack(project_folder: Path) -> dict:
    return TechFacade().detect_stack(project_folder)
