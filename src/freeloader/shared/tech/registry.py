import importlib

from .base import TechDetector


_REGISTRY: dict[str, type[TechDetector]] = {}


def tech_detector(name: str):
    def decorator(cls: type[TechDetector]) -> type[TechDetector]:
        _REGISTRY[name] = cls
        return cls
    return decorator


def load_detectors() -> dict[str, TechDetector]:
    importlib.import_module(".detectors", __package__)

    return {name: cls() for name, cls in _REGISTRY.items()}
