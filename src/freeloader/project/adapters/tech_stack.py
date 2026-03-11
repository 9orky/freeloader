from pathlib import Path

from freeloader.shared.tech import TechFacade

from ..models import TechStack


def detect_stack(project_folder: Path) -> TechStack | None:
    detected = TechFacade().detect_stack(project_folder)
    if not detected:
        return None
    return TechStack.model_validate(detected)
