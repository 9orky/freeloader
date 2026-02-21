from pathlib import Path

from .registry import TechStack


def detect(project_dir: Path) -> TechStack | None:
    from .registry import detect_stack
    return detect_stack(Path(project_dir))
