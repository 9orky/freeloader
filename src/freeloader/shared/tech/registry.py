from pathlib import Path

from .base import TechDetector, TechStack


_REGISTRY: dict[str, type[TechDetector]] = {}


def tech_detector(name: str):
    def decorator(cls: type[TechDetector]) -> type[TechDetector]:
        _REGISTRY[name] = cls
        return cls
    return decorator


def detect_stack(project_dir: Path) -> TechStack | None:
    for detector_cls in _REGISTRY.values():
        result = detector_cls().detect(project_dir)
        if result:
            return result
    return None
