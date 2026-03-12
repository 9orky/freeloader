from pathlib import Path

from .base import TechDetector, TechStack
from .registry import load_detectors


class TechFacade:
    def __init__(self) -> None:
        self._detectors: dict[str, TechDetector] = load_detectors()

    def detect_stack(self, project_dir: Path) -> TechStack | None:
        for detector in self._detectors.values():
            result = detector.detect(project_dir)
            if result:
                return result

        return None

        # Here you would implement logic to create test projects
        # for each combination of language, package manager, and framework.
        # This is a placeholder for demonstration purposes.
        # project_path = test_projects_dir / detector.language / pm.name / fm.name
        # project_path.mkdir(parents=True, exist_ok=True)
        # graph[detector.language][pm.name][fm.name].append(str(project_path))
