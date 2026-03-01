from .base import TechDetector
from .registry import load_detectors
from . import detectors


class TechFacade:
    def __init__(self) -> None:
        self._detectors: dict[str, TechDetector] = load_detectors()

    def detect_stack(self, project_dir) -> dict:
        for detector in self._detectors.values():
            result = detector.detect(project_dir)
            if result:
                return result.to_dict()

        return {}
