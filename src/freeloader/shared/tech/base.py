from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Protocol


class PackageManager(Protocol):
    name: str
    patterns: list[str] = []
    match_all: bool = False


@dataclass(frozen=True)
class TechStack:
    language: str
    package_manager: str

    def to_dict(self) -> dict:
        return asdict(self)


class TechDetector(Protocol):
    language: str
    package_managers: list[type[PackageManager]]

    def _file_exists(self, pattern: str, project_dir: Path) -> bool:
        if not list(project_dir.glob(pattern)):
            return False
        return True

    def detect(self, project_dir: Path) -> TechStack | None:
        for pm in self.package_managers:
            matches = [self._file_exists(p, project_dir) for p in pm.patterns]
            if pm.match_all and all(matches):
                return TechStack(language=self.language, package_manager=pm.name)
            elif not pm.match_all and any(matches):
                return TechStack(language=self.language, package_manager=pm.name)
        
        return None