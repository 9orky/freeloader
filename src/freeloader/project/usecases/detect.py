from pathlib import Path

from ..adapters import tech_stack as tech_stack_adapter
from ..models import TechStack


def detect_project_stack(project_folder: Path) -> TechStack | None:
    return tech_stack_adapter.detect_stack(project_folder)
