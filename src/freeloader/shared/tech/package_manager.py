import json
import re
import tomllib
from pathlib import Path
from typing import Iterable, Literal, Protocol


class PackageFileReader(Protocol):
    def read_txt(self, pattern: str, project_dir: Path) -> Iterable[str]: ...
    def read_json(self, pattern: str, project_dir: Path) -> dict | None: ...
    def read_toml(self, pattern: str, project_dir: Path) -> dict | None: ...


class DefaultPackageFileReader:
    def read_txt(self, pattern: str, project_dir: Path) -> Iterable[str]:
        for file in project_dir.glob(pattern):
            with file.open() as f:
                yield from f

    def read_json(self, pattern: str, project_dir: Path) -> dict | None:
        for file in project_dir.glob(pattern):
            with file.open() as f:
                return json.load(f)
        return None

    def read_toml(self, pattern: str, project_dir: Path) -> dict | None:
        for file in project_dir.glob(pattern):
            with file.open("rb") as f:
                return tomllib.load(f)
        return None


class PackageManager(Protocol):
    name: str
    patterns: list[str]
    command_templates: dict[Literal["init", "install", "update", "add", "remove"], str]
    match_all: bool = True
    manager_filename: str | None = None
    package_pattern_template: str | None = None
    language_version_pattern: str | None = None

    def recognizes(self, project_dir: Path) -> bool:
        matches = [bool(list(project_dir.glob(p))) for p in self.patterns]
        if self.match_all:
            return all(matches)
        return any(matches)
    
    def read_manager_file(self, project_dir: Path) -> str:
        filename = self.manager_filename or self.patterns[0]
        file_path = Path(project_dir) / filename

        assert file_path.exists(), f"Expected {filename} not found in {project_dir}"
        return file_path.read_text().strip()
    
    def extract_language_version(self, project_dir: Path) -> str | None:
        if self.language_version_pattern:
            file_content = self.read_manager_file(project_dir)
            match = re.search(self.language_version_pattern, file_content)
            if match:
                return match.group(1)
        return None
