from pathlib import Path
from os import getenv

from .base import TechDetector
from .registry import load_detectors
from . import detectors


class TechFacade:
    def __init__(self) -> None:
        self._detectors: dict[str, TechDetector] = load_detectors()

    def detect_stack(self, project_dir: Path) -> dict:
        for detector in self._detectors.values():
            result = detector.detect(project_dir)
            if result:
                return result.to_dict()

        return {}
    
    def build_graph(self, test_projects_dir: Path) -> dict:
        assert test_projects_dir.exists(), "Test projects directory does not exist."
        graph = {}
        
        for detector in self._detectors.values():
            if detector.language not in graph:
                graph[detector.language] = {}

            for pm_cls in detector.package_managers:
                pm = pm_cls()
                graph[detector.language][pm.name] = {}

                for fm_cls in detector.frameworks:
                    fm = fm_cls()
                    graph[detector.language][pm.name][fm.name] = {}

                    for command, template in pm.command_templates.items():
                        command_str = template.format(package=fm.name)
                        graph[detector.language][pm.name][fm.name][command] = command_str
        
        return graph

                    # Here you would implement logic to create test projects
                    # for each combination of language, package manager, and framework.
                    # This is a placeholder for demonstration purposes.
                    # project_path = test_projects_dir / detector.language / pm.name / fm.name
                    # project_path.mkdir(parents=True, exist_ok=True)
                    # graph[detector.language][pm.name][fm.name].append(str(project_path))
