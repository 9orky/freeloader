from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

from .language import LanguageSource
from .package_manager import PackageManager
from .framework import Framework


@dataclass(frozen=True)
class TechStack:
    language: str
    language_version: str | None = None
    package_manager: str | None = None
    framework: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


class TechDetector(Protocol):
    language: str
    package_managers: list[type[PackageManager]]
    language_sources: list[type[LanguageSource]]
    frameworks: list[type[Framework]]

    def detect(self, project_dir: Path) -> TechStack | None:
        detections: dict[str, str | None] = {
            "language_version": None, 
            "package_manager": None, 
            "framework": None,
        }

        for pm_cls in self.package_managers:
            pm = pm_cls()
            if pm.recognizes(project_dir):
                detections["language"] = self.language
                detections["package_manager"] = pm.name
                manager_file_content = pm.read_manager_file(project_dir)

                if pm.language_version_pattern:
                    detections["language_version"] = pm.extract_language_version(project_dir)
                
                for fm_cls in self.frameworks:
                    fm = fm_cls()

                    if pm.package_pattern_template:
                        pattern = pm.package_pattern_template.format(package=fm.name)
                        fm.file_line_pattern = pattern
            
                    if fm.detect(manager_file_content):
                        detections["framework"] = fm.name
                        break
            
                if detections["language_version"] is None:
                    for lang_source_cls in self.language_sources:
                        lang_source = lang_source_cls()
                        version = lang_source.detect(project_dir)
                        if version:
                            detections["language_version"] = version
                            break                    

            if "language" in detections:
                return TechStack(**detections)