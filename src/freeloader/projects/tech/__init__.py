from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class TechStack:
    language: str
    package_manager: str
    framework: str = ""
    dockerfile_template: str = ""
    ci_templates: list[str] = field(default_factory=list)


class TechDetector(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def patterns(self) -> list[str]: ...

    @abstractmethod
    def analyze(self, matched: dict[str, list[Path]]) -> TechStack | None: ...

    def detect(self, project_dir: Path) -> TechStack | None:
        matched: dict[str, list[Path]] = {}
        for pattern in self.patterns:
            hits = list(project_dir.glob(pattern))
            if hits:
                matched[pattern] = hits
        if not matched:
            return None
        return self.analyze(matched)

    @staticmethod
    def read_text(path: Path) -> str:
        return path.read_text(encoding="utf-8")

    @staticmethod
    def contains(path: Path, needle: str) -> bool:
        return needle in path.read_text(encoding="utf-8")


_REGISTRY: list[type[TechDetector]] = []


def tech_detector(cls: type[TechDetector]) -> type[TechDetector]:
    _REGISTRY.append(cls)
    return cls


def detect_stack(project_dir: Path) -> TechStack | None:
    for detector_cls in _REGISTRY:
        result = detector_cls().detect(project_dir)
        if result:
            return result
    return None


from freeloader.projects.tech import node, python, go, rust  # noqa: E402, F401
